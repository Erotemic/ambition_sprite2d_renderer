"""Giant spider: a dark, hairy hunting spider with eight articulated legs.

The legs plant in alternating groups. The first pair lifts when the spider
notices a target. It draws back and opens its fangs before it strikes.
Every leg is composed of reusable jointed parts; side, three-quarter and
front views have independently authored body geometry and leg targets.
"""
from __future__ import annotations

import math
from contextlib import contextmanager
from pathlib import Path

from PIL import Image
import numpy as np

from ._magic_character_art import Canvas, add, sub, mul, mix, unit, perp, rot, bezier, phase, track
from ...authoring.sheet_build import build_sheet
from ...authoring import rigdoc
from ...authoring.part_flipbook import publish_rig_flipbook
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'giant_spider'
SIDE_FRAME_SIZE = (272, 200)
# Transparent padding keeps reflected poses inside the canvas.
FRAME_SIZE = (336, 200)
SIDE_PAD = 32
GROUND = 168.0
# The core and its ground clearance define the body, not the leg span.
BODY_BOX = (77, 86, 223, 170)
ROWS = [('idle', 12, 100), ('walk', 16, 65), ('run', 16, 45),
        ('turnaround', 5, 44), ('notice', 8, 70), ('windup', 8, 60), ('attack_side', 12, 50),
        ('hit', 8, 55), ('death', 18, 65), ('death_idle', 6, 150)]
LOOPS = {'idle', 'walk', 'run', 'windup', 'death_idle'}
TRAITS = ['enemy', 'fantasy', 'monster', 'spider', 'arachnid']
ACTOR_METADATA = {
    'actor': {'character_id': TARGET_NAME, 'display_name': 'Giant Spider'},
    'body': {'body_plan': 'Multileg', 'body_kind': 'Standard',
             'mass_class': 'Medium', 'locomotion_hint': 'Walk', 'traits': TRAITS},
    'capabilities': {'traversal': {'walk': True}},
    'actions': {'default_preset': 'giant_spider_bite'},
    'visual': {'default_pose': 'idle', 'portrait': {'animation': 'idle', 'frame': 0}},
    'animation_bindings': {
        'default': {'animation': 'idle', 'events': []},
        'locomotion.walk': {'animation': 'walk', 'events': []},
        'locomotion.run': {'animation': 'run', 'events': []},
        'locomotion.turnaround': {'animation': 'turnaround', 'events': []},
        'action.melee.primary': {'animation': 'attack_side', 'events': [
            {'t': 0.0, 'event': 'hitbox_active_start', 'source': 'giant_spider.bite'},
            {'t': .14 / .60, 'event': 'hitbox_active_end', 'source': 'giant_spider.bite'}]},
        'combat.hurt': {'animation': 'hit', 'events': []},
        'combat.death': {'animation': 'death', 'events': []},
    },
    'tags': TRAITS,
    'authoring_description': 'A dark brown hunting spider with eight jointed legs, a mottled abdomen, clustered amber eyes and hooked fangs.',
    'gameplay_description': 'It lifts its front legs when it sees a target. It rears, strikes with its fangs and scuttles away.',
}

INK = '#241c22'
FAR_INK = '#30262b'
LEG = '#61483e'
LEG_LIGHT = '#997560'
LEG_DARK = '#443237'
FAR_LEG = '#49383a'
FAR_LIGHT = '#6a5148'
SHELL = '#59413b'
SHELL_LIGHT = '#88624f'
SHELL_DARK = '#3c2b2b'
HAIR = '#aa8167'
FANG = '#c6a68a'
EYE = '#e7a24e'


def _curve(points):
    out = [points[0]]
    for k in range(1, len(points), 3):
        out.extend(bezier(out[-1], *points[k:k + 3], n=14)[1:])
    return out


def _shape(c, points, color, edge=INK, width=1.9):
    c.poly(_curve(points), color, edge, width)


def _segment(c, a, b, ra, rb, color, light, edge):
    """A tapered leg segment, with a highlight on its own surface."""
    n = perp(unit(sub(b, a)))
    left = [add(a, mul(n, ra)), add(b, mul(n, rb))]
    right = [add(a, mul(n, -ra)), add(b, mul(n, -rb))]
    c.poly(left + right[::-1], color, edge, 1.5)
    c.line([mix(left[0], right[0], .25), mix(left[1], right[1], .25)], light, 1.15)
    # Small bristles stay attached to the segment as it moves.
    for t in (.24, .49, .74):
        r = ra + (rb-ra)*t
        p = mix(a, b, t)
        d = unit(sub(b, a))
        q = add(p, mul(n, r))
        c.line([q, add(add(q, mul(n, 3.0)), mul(d, -2.0))], color, .95)
        q = add(p, mul(n, -r))
        c.line([q, add(add(q, mul(n, -2.6)), mul(d, -2.0))], light, .85)


class PartScene:
    """Record reusable local rasters, in the same order as the preview paint.

    Joint targets are calculated in world pixels. Segment length changes use
    local-axis scaling; no full character image is ever used as a part.
    """
    _cache = {}
    s = 3
    # Enough space to draw an entire anatomical part about its local pivot.
    local_size = (384, 280)
    center = (192, 100)

    def __init__(self):
        self.ops = []
        self.local = None
        self.anchor = None
        self.cached = False

    @contextmanager
    def part(self, name, anchor=(0.,0.), *, key=None, at=None,
             degrees=0., scale_y=1.):
        assert self.anchor is None, name
        self.anchor = anchor
        cache = self._cache.get(key) if key is not None else None
        self.cached = cache is not None
        self.local = None if self.cached else Canvas(self.local_size, self.s)
        try:
            yield
            if cache is None:
                im = self.local.image
                bbox = im.getbbox()
                if bbox is None:
                    return
                x0,y0,x1,y1 = bbox
                assert x0>0 and y0>0 and x1<im.width and y1<im.height, name
                x0 = (x0-6)//self.s*self.s
                y0 = (y0-6)//self.s*self.s
                x1 = math.ceil((x1+6)/self.s)*self.s
                y1 = math.ceil((y1+6)/self.s)*self.s
                pivot = (self.center[0]*self.s-x0, self.center[1]*self.s-y0)
                cache = (im.crop((x0,y0,x1,y1)),pivot)
                if key is not None:
                    self._cache[key] = cache
            dest = tuple(round(v)*self.s for v in (anchor if at is None else at))
            self.ops.append((name,*cache,dest,degrees,scale_y))
        finally:
            self.local = self.anchor = None
            self.cached = False

    def _pt(self, p):
        return (p[0]-self.anchor[0]+self.center[0],
                p[1]-self.anchor[1]+self.center[1])

    def poly(self, pts, color, edge=INK, w=1.8):
        if not self.cached:
            self.local.poly([self._pt(v) for v in pts], color, edge, w)

    def line(self, pts, color, w=1.5):
        if not self.cached:
            self.local.line([self._pt(v) for v in pts], color, w)

    def oval(self, p, rx, ry, fill, edge=INK, w=1.5, angle=0):
        if not self.cached:
            self.local.oval(self._pt(p),rx,ry,fill,edge,w,angle)

    def disk(self, p, r, fill, edge=INK, w=1.5):
        self.oval(p,r,r,fill,edge,w)

    def finish(self, ground_lock=False):
        frame = Image.new('RGBA', tuple(v*self.s for v in FRAME_SIZE))
        dy = 0
        if ground_lock:
            bottom = -math.inf
            for _,im,pivot,at,deg,sy in self.ops:
                yy,xx = np.nonzero(np.asarray(im.getchannel('A'))>=32)
                if len(yy):
                    r = math.radians(deg)
                    support = (xx-pivot[0])*math.sin(r)+(yy-pivot[1])*sy*math.cos(r)
                    bottom = max(bottom, at[1]+float(support.max())+1)
            dy = round((GROUND+1)*self.s-bottom)
        for name,im,pivot,at,deg,sy in self.ops:
            rigdoc.blit_rotated(frame,im,pivot,(at[0],at[1]+dy),deg,
                                part_name=name,scale_y=sy)
        return rigdoc.downsampled_canvas(frame,FRAME_SIZE,Image.Resampling.LANCZOS)


def _leg_segment(scene, name, a, b, role, near):
    """A rigid hairy segment about its proximal joint, with overlapped ends.

    Small length families limit local-axis stretch, preserving the bristle
    silhouette. The distal cap of the femur covers the tibia seam.
    """
    dx,dy = sub(b,a)
    length = max(.5,math.hypot(dx,dy))
    # Reuse discrete raster lengths across poses; choose
    # a six-pixel bucket to keep hairs and joint radii roughly constant.
    L = max(6, 6*round(length/6))
    angle = math.degrees(math.atan2(-dx,dy))
    radii = {'coxa':(5.2,5.0),'femur':(5.2,3.9),
             'tibia':(3.9,2.2),'tarsus':(2.1,.7)}
    ra,rb = radii[role]
    if not near:
        ra,rb = ra*.77,rb*.80
    col,light,edge = (LEG,LEG_LIGHT,INK) if near else (FAR_LEG,FAR_LIGHT,FAR_INK)
    if role=='tarsus' and near:
        col=LEG_DARK
    with scene.part(name, key=('leg',role,near,L), at=a, degrees=angle,
                    scale_y=length/L):
        # Draw local +y with the same tapered, bristled surface vocabulary
        # as the previous whole-frame spider, then cap only the joints.
        _segment(scene,(0,-min(ra*.45,L*.18)),(0,L),ra,rb,col,light,edge)
        if role=='femur':
            scene.disk((0,L),rb*.93,LEG_DARK if near else FAR_LEG,edge,1.05)
            scene.line([(-rb*.55,L-2.8),(0,L-.8),(rb*.45,L)],light,.9)
        elif role=='coxa':
            scene.disk((0,L),rb*.85,col,None)
            scene.line([(ra*.35,0),(rb*.5,L-1)],light,.9)


def _leg_chain(scene, name, root, coxa, knee, foot, near, bend=1.):
    ankle = add(mix(knee,foot,.80),mul(perp(unit(sub(foot,knee))),3.3*bend))
    # All four bones of a leg stay together in painter order; the next leg
    # can occlude the entire chain, not just one of its bones.
    for role,a,b in [('tarsus',ankle,foot),('tibia',knee,ankle),
                     ('femur',coxa,knee),('coxa',root,coxa)]:
        _leg_segment(scene,f'{name}_{role}',a,b,role,near)


def _render_side_frame(anim, i, n):
    t = phase(i, n, anim in LOOPS)
    cyc = math.tau*t
    gait = 0.0
    bob = 1.1*math.sin(cyc)
    rear = strike = recoil = curl = 0.0
    gape = .12 + .06*math.sin(cyc)
    alarm = 0.0
    if anim in ('walk', 'run'):
        gait = 1.0 if anim == 'walk' else 1.55
        bob = -1.7*gait*math.cos(2*cyc)
    elif anim == 'notice':
        alarm = track(t, [(0,.48),(.35,1),(1,.8)])
        rear = .54*alarm
        gape = .4*alarm
        bob = 0
    elif anim == 'windup':
        rear = .98 + .02*math.sin(cyc)
        gape = .9 + .08*math.sin(cyc)
        bob = 0
    elif anim == 'attack_side':
        # The active strike comes first. The rest of the row is recovery.
        strike = track(t, [(0,.9),(.12,1),(.20,.87),(.42,.43),(.72,.08),(1,0)])
        gape = track(t, [(0,.95),(.12,.75),(.20,.05),(.35,.2),(1,.12)])
        rear = track(t, [(0,.12),(.2,0),(.75,.08),(1,0)])
        bob = 0
    elif anim == 'hit':
        recoil = track(t, [(0,.75),(.2,1),(.58,.35),(1,0)])
        gape = .7*recoil
        bob = 0
    elif anim in ('death','death_idle'):
        curl = track(t, [(0,0),(.12,.10),(.36,.45),(.77,1),(1,1)]) if anim=='death' else 1.0
        recoil = .65*math.sin(math.pi*min(1,t*2.6)) if anim=='death' else 0
        gape = track(t, [(0,.7),(.28,1),(.65,.4),(1,.05)]) if anim=='death' else .05
        bob = 0
    c = PartScene()
    origin = (SIDE_PAD + 134 - 8*rear + 14*strike - 7*recoil, 123 + bob + 19*curl - 5*rear)
    pitch = -18*rear + 10*strike - 9*recoil + 10*curl

    def B(x,y):
        return add(origin, rot((x,y), pitch))
    def oval(x,y,rx,ry,color,edge=INK,w=1.7,angle=0):
        c.oval((x,y),rx,ry,color,edge,w,angle)
    def shape(pts,color,edge=INK,w=1.9):
        _shape(c,pts,color,edge,w)
    def line(pts,color,w=1.4):
        c.line(pts,color,w)

    # A right-facing three-quarter projection. Each leg has its own coxa,
    # femur, knee, tibia, and tarsus. Keep the face clear of the near front
    # femur: it first extends out of the lower carapace before rising.
    # Far-side knees and feet have a different silhouette, not a copy of
    # the near-side chain displaced by a few pixels.
    def leg(k, near):
        roots = ((24,12),(9,15),(-3,14),(-15,9)) if near else ((23,-3),(10,-5),(-2,-4),(-13,-2))
        coxae = ((39,16),(8,20),(-13,18),(-27,12)) if near else ((34,-12),(16,-14),(-12,-14),(-25,-11))
        knees = ((66,-25),(-8,-35),(-37,-34),(-66,-20)) if near else ((50,-43),(17,-49),(-26,-45),(-58,-35))
        feet = (245,151,100,38) if near else (221,184,77,29)
        gy = GROUND if near else GROUND-13
        root, coxa = B(*roots[k]), B(*coxae[k])
        fx, fy = feet[k], gy
        if gait:
            p = cyc + (0 if (k % 2 == 0)==near else math.pi)
            fx += 11*gait*math.cos(p)
            fy -= 12*gait*max(0,math.sin(p))
        if k == 0:
            fx += 4*rear + 8*strike
            fy -= (63 if near else 49)*rear + 10*strike
        elif k == 1:
            fx += 5*rear + 5*strike
            fy -= (21 if near else 15)*rear
        fx += (k-1.5)*3*recoil
        kx,ky = knees[k]
        knee = B(kx + .31*(fx-feet[k]), ky - .20*(gy-fy))
        if rear and k == 0:
            knee = mix(knee,B(55 if near else 36,-43 if near else -54),rear)
        if strike and k == 0:
            knee = mix(knee,B(72 if near else 53,-15 if near else -21),strike)
        foot = (fx+SIDE_PAD,fy)
        if curl:
            # The rear legs fold backwards; front legs curl towards the
            # underside. Keep the two folded silhouettes staggered in depth.
            fold_coxae = ((32,12),(10,20),(-14,18),(-29,9)) if near else ((29,-8),(9,-15),(-13,-14),(-27,-10))
            fold_knees = ((48,-15),(-3,-25),(-29,-23),(-48,-10)) if near else ((38,-23),(21,-34),(-19,-32),(-43,-22))
            fold_feet = ((24,17),(4,25),(-16,23),(-33,14)) if near else ((22,5),(7,12),(-12,11),(-31,4))
            coxa = mix(coxa,B(*fold_coxae[k]),curl)
            knee = mix(knee,B(*fold_knees[k]),curl)
            foot = mix(foot,B(*fold_feet[k]),curl)
            foot = (foot[0],min(gy,foot[1]))
        _leg_chain(c,f'{"near" if near else "far"}_{k}',root,coxa,knee,foot,near,
                   1 if k<2 else -1)

    for k in (3,2,1,0):
        leg(k,False)

    # Pedicel and abdomen. The belly is rounded; the upper plate has
    # a muted mottled pattern. Hair follows the silhouette of the abdomen.
    with c.part('abdomen', key=('side','abdomen'), at=origin, degrees=pitch):
        oval(-18,0,14,10,SHELL_DARK)
        abdomen = [(-17,-10),(-19,-31),(-43,-39),(-65,-34),(-87,-30),(-94,-12),(-88,7),
                   (-83,25),(-58,31),(-37,23),(-25,20),(-15,10),(-17,-10)]
        shape(abdomen,SHELL,INK,2.5)
        shape([(-87,-7),(-88,-26),(-64,-34),(-42,-29),(-28,-24),(-25,-18),(-24,-13),
               (-52,-23),(-69,-18),(-78,-6),(-83,-1),(-86,-3),(-87,-7)],SHELL_LIGHT,None)
        shape([(-88,4),(-79,13),(-67,17),(-51,17),(-36,16),(-26,8),(-20,3),
               (-26,22),(-52,30),(-67,24),(-80,21),(-87,15),(-88,4)],SHELL_DARK,None)
        for x,y in [(-73,-21),(-56,-25),(-39,-19),(-70,5),(-50,7),(-31,1)]:
            oval(x,y,7,3.0,'#6b493d',None,angle=-12)
        for j in range(18):
            a = math.radians(85+15*j)
            p = (-54+34*math.cos(a),-3+26*math.sin(a))
            q = add(p,(4.3*math.cos(a),4.0*math.sin(a)))
            line([p,q],HAIR if j>6 else LEG_DARK,1.0)
        for x,y in [(-82,-12),(-73,-18),(-67,-11),(-59,-20),(-48,-14),(-39,-9),(-76,1),(-61,8),(-44,8)]:
            line([(x,y),(x+4,y-2)],'#ad8263',.85)
        # Spinnerets sit at the rear of the abdomen.
        oval(-86,11,5,3,SHELL_DARK,INK,1.1,angle=-22)

    # The front body has a raised carapace and a low face, rather than a
    # separate humanoid head. Draw the near legs over the lower body plate.
    with c.part('carapace', key=('side','carapace'), at=origin, degrees=pitch):
        shape([(-23,2),(-22,-20),(-7,-28),(17,-22),(29,-19),(42,-6),(41,7),
               (39,22),(20,24),(1,20),(-14,18),(-23,13),(-23,2)],SHELL,INK,2.4)
        shape([(-17,-5),(-15,-18),(-4,-22),(13,-19),(24,-17),(32,-11),(33,-6),
               (15,-13),(1,-12),(-7,-4),(-12,0),(-16,-1),(-17,-5)],SHELL_LIGHT,None)
        line([(-18,6),(-8,12),(8,15),(26,13)],SHELL_DARK,2.2)
    # Eyes occupy their own face plate, outside the near leg chains. A pair of larger forward eyes and
    # six small eyes give the head the anatomy of a hunting spider.
    eye_state = 'dark' if curl>=.72 else 'dim' if curl>=.32 or recoil>=.6 else 'bright'
    with c.part('eye_plate', key=('side','eyes',eye_state), at=origin, degrees=pitch):
        shape([(13,-12),(20,-18),(31,-15),(36,-8),(40,-3),(37,2),(32,4),
               (22,4),(13,0),(13,-12)],'#36282a',None)
        eyes = [(22,-7,4.8,4.2),(34,-5,4.2,3.8),(15,-14,2.6,2.3),
                (23,-16,2.7,2.4),(31,-14,2.6,2.4),(37,-11,2.0,2.1),
                (14,1,1.9,1.8),(29,3,1.8,1.6)]
        for x,y,rx,ry in eyes:
            oval(x,y,rx,ry,'#211a21',INK,1.0)
            if curl<.72:
                color = EYE if curl<.32 and recoil<.6 else '#99623c'
                oval(x+.5,y,rx*.72,ry*.73,color,None)
                if rx>3:
                    oval(x+1.1,y+.25,rx*.28,ry*.61,'#35222a',None)
                    oval(x-.8,y-1.1,rx*.20,ry*.21,'#f7d19c',None)
                else:
                    oval(x-.5,y-.6,rx*.22,ry*.23,'#f3c18a',None)
    # The two chelicerae and their curved fangs move as distinct parts.
    def fang(near):
        x,y = (35,8) if near else (41,3)
        spread = gape*(11 if near else 7)
        s = 1 if near else -1
        a = (x,y)
        b = (x+7+spread,y+5+s*spread*.24)
        d = (x+9+spread,y+13+s*spread*.7)
        e = (x+3+spread,y+17+s*spread*.8)
        line([a,b],INK,9 if near else 7)
        line([a,b],SHELL_DARK if near else FAR_LEG,6 if near else 4.6)
        shape([b,(b[0]+4,b[1]),(d[0]+4,d[1]-2),d,(d[0]-1,d[1]+3),(e[0]+2,e[1]+1),e,
               (e[0]+1,e[1]-4),(b[0]-1,b[1]+4),b],FANG if near else '#8f7464',INK,1.3)
    # Quantized gape variants remain independent of the rest of the head.
    gape = round(gape*5)/5
    with c.part('chelicera_far',key=('side','fang',False,gape),at=origin,degrees=pitch):
        fang(False)
    with c.part('pedipalp',key=('side','palp'),at=origin,degrees=pitch):
        oval(27,11,5.2,6.2,LEG_DARK,INK,1.1,angle=-30)
    with c.part('chelicera_near',key=('side','fang',True,gape),at=origin,degrees=pitch):
        fang(True)
    # Foreground legs overlay the carapace, abdomen, and face if their
    # projected geometry actually crosses them. Rear legs remain behind.
    for k in (3,2,1,0):
        leg(k,True)
    return c.finish(ground_lock=anim in ('death','death_idle'))


def _front_frame():
    """Head-on elevated view. Eight separately projected articulated legs."""
    c=PartScene()
    cx=(BODY_BOX[0]+BODY_BOX[2]-1)/2
    def P(x,y): return (cx+x,y)
    def pts(seq,s=1): return [P(s*x,y) for x,y in seq]
    def shape(seq,col,edge=INK,w=1.9,s=1): _shape(c,pts(seq,s),col,edge,w)
    def oval(x,y,rx,ry,col,edge=INK,w=1.7,angle=0): c.oval(P(x,y),rx,ry,col,edge,w,angle)
    def line(seq,col=INK,w=1.4,s=1): c.line(pts(seq,s),col,w)
    # Each successive pair is nearer the viewer. The knees fan out along
    # different rays; the four tarsi on each side land on separate rows.
    # The front pair stays outside the eye plate and the two fangs.
    legs=[((17,106),(29,103),(47,68),(60,137)),
          ((23,114),(37,110),(79,69),(94,145)),
          ((26,122),(42,122),(104,87),(119,158)),
          ((27,133),(43,138),(66,120),(82,168))]
    def leg(k,s):
        a,b,d,e=pts(legs[k],s)
        _leg_chain(c,f'front_{s}_{k}',a,b,d,e,k>=2,s*.8)
    for k in (0,1):
        for s in (-1,1): leg(k,s)
    # Abdomen is seen behind and above the cephalothorax. The pedicel
    # disappears behind the front body, not between the eyes.
    with c.part('front_abdomen', (cx,106), key=('front','abdomen')):
        oval(0,109,13,10,SHELL_DARK)
        shape([(0,75),(22,73),(36,84),(38,100),(41,116),(27,133),(0,136),
               (-27,133),(-41,116),(-38,100),(-36,84),(-22,73),(0,75)],SHELL,INK,2.5)
        shape([(-33,98),(-30,82),(-13,78),(0,79),(13,77),(30,83),(33,98),
               (13,91),(-12,91),(-33,98)],SHELL_LIGHT,None)
        shape([(-35,111),(-26,121),(-12,124),(0,124),(12,124),(26,121),(35,111),
               (31,132),(12,135),(0,135),(-12,135),(-31,132),(-35,111)],SHELL_DARK,None)
        for x,y,ang in [(-22,87,24),(-7,84,-7),(13,87,-20),(27,95,38),(-26,103,16),(8,100,-16)]:
            oval(x,y,6.5,3,'#6b493d',None,angle=ang)
        for j in range(19):
            a=math.radians(188+9*j)
            x,y=37*math.cos(a),103+27*math.sin(a)
            line([(x,y),(x+4*math.cos(a),y+4*math.sin(a))],HAIR,1)
        for x,y in [(-29,88),(-17,82),(-5,81),(10,84),(25,90),(-30,101),(30,104)]:
            line([(x,y),(x+2,y-3)],'#ad8263',.85)
    # Cephalothorax, viewed head-on, with a raised carapace and broad
    # low eye plate. The eye pattern preserves the two dominant eyes.
    with c.part('front_carapace',(cx,126),key=('front','carapace')):
        shape([(0,100),(20,100),(34,111),(35,125),(37,141),(22,152),(0,152),
               (-22,152),(-37,141),(-35,125),(-34,111),(-20,100),(0,100)],SHELL,INK,2.4)
        shape([(-29,118),(-26,107),(-11,104),(0,105),(11,104),(26,107),(29,118),
               (16,113),(-16,113),(-29,118)],SHELL_LIGHT,None)
    with c.part('front_eye_plate',(cx,126),key=('front','eyes')):
        shape([(-23,121),(-20,112),(-8,114),(0,114),(8,114),(20,112),(23,121),
               (26,134),(13,142),(0,141),(-13,142),(-26,134),(-23,121)],'#36282a',None)
        for s in (-1,1):
            for x,y,rx,ry in [(9,126,5.1,4.8),(19,128,3.2,3.1),(7,117,2.7,2.4),(18,117,2.5,2.2)]:
                oval(s*x,y,rx,ry,'#211a21',INK,1)
                oval(s*x,y,rx*.74,ry*.74,EYE,None)
                if rx>3:
                    oval(s*x,y+.25,rx*.29,ry*.62,'#35222a',None)
                oval(s*x-.9,y-1.05,rx*.20,ry*.21,'#f7d19c',None)
    # Each chelicera and its fang hangs below the eyes. Small palps are
    # separate from (and visibly shorter than) the eight walking legs.
    for s in (-1,1):
        with c.part(f'front_chelicera_{s}',(cx,147),key=('front','fang',s)):
            oval(s*22,143,5.2,6.2,LEG_DARK,INK,1.1,angle=s*25)
            shape([(6,140),(8,136),(14,137),(16,142),(17,147),(13,152),(9,151),
                   (6,149),(4,144),(6,140)],SHELL_DARK,INK,1.5,s)
            shape([(9,148),(13,147),(16,151),(15,155),(14,161),(10,164),(5,164),
                   (9,160),(11,154),(9,148)],FANG,INK,1.3,s)
            line([(12,150),(13,154),(10,160)],'#e0bfa4',.9,s)
    # Foreground leg chains overlap the lower side of the carapace only.
    for k in (2,3):
        for s in (-1,1): leg(k,s)
    return c.finish()


def _quarter_frame():
    """A genuine, elevated three-quarter view, facing down and right.

    The abdomen recedes diagonally behind the face. Both eye banks and
    chelicerae are visible, but the far bank is smaller and partly recessed.
    Eight distinct leg paths are projected onto the ground plane; these
    are authored joint targets, not a warp of either adjacent view.
    """
    c = PartScene()
    cx = (BODY_BOX[0]+BODY_BOX[2]-1)/2
    def P(x,y): return (cx+x,y)
    def shape(seq,col,edge=INK,w=1.9): _shape(c,[P(*p) for p in seq],col,edge,w)
    def oval(x,y,rx,ry,col,edge=INK,w=1.7,angle=0): c.oval(P(x,y),rx,ry,col,edge,w,angle)
    def line(seq,col=INK,w=1.4): c.line([P(*p) for p in seq],col,w)

    # Front to rear on each side. Near roots form a curved arc across the
    # lower cephalothorax; far roots sit up and to its right. Feet step
    # farther back on the ground plane as their depth increases.
    near_legs = [((24,137),(39,143),(68,108),(96,168)),
                 ((9,137),(-2,144),(-13,100),(5,169)),
                 ((-3,131),(-24,136),(-45,89),(-47,163)),
                 ((-11,121),(-31,125),(-73,96),(-91,153))]
    far_legs = [((37,118),(49,111),(80,80),(110,149)),
                ((26,109),(39,99),(53,65),(72,137)),
                ((13,105),(15,92),(16,60),(31,127)),
                ((1,105),(-16,94),(-33,66),(-55,130))]
    for k in (3,2,1,0):
        _leg_chain(c,f'quarter_far_{k}',*(P(*v) for v in far_legs[k]),False,
                   1 if k<2 else -1)

    with c.part('quarter_abdomen',(cx-30,102),key=('quarter','abdomen')):
        # In this projection the pedicel points diagonally into the rear
        # of the front body. The far half of the abdomen is foreshortened.
        oval(-9,113,14,10,SHELL_DARK,angle=25)
        shape([(-1,88),(-15,69),(-41,67),(-58,79),
               (-78,94),(-78,117),(-58,131),
               (-39,145),(-9,137),(2,121),
               (14,108),(9,96),(-1,88)],SHELL,INK,2.5)
        shape([(-67,96),(-63,80),(-40,73),(-24,77),
               (-11,80),(-4,87),(-1,96),
               (-21,85),(-43,88),(-55,100),
               (-61,104),(-65,101),(-67,96)],SHELL_LIGHT,None)
        shape([(-71,110),(-54,122),(-37,127),(-23,122),
               (-9,119),(1,113),(8,106),
               (8,126),(-12,140),(-35,137),
               (-52,137),(-68,124),(-71,110)],SHELL_DARK,None)
        for x,y,rx,ry,ang in [(-53,85,7,3,27),(-37,82,7,3,-3),
                               (-20,88,6,3,24),(-61,106,6,3,25),
                               (-41,105,7,3,18),(-21,113,6,3,22)]:
            oval(x,y,rx,ry,'#6b493d',None,angle=ang)
        for j in range(19):
            a=math.radians(76+14*j)
            x,y=-30+39*math.cos(a),105+30*math.sin(a)
            line([(x,y),(x+4*math.cos(a),y+4*math.sin(a))],
                 HAIR if j>6 else LEG_DARK,1.)
        for x,y in [(-58,87),(-47,79),(-33,82),(-24,87),(-15,95),
                    (-64,101),(-51,112),(-32,117)]:
            line([(x,y),(x+3,y-2.4)],'#ad8263',.85)
        # The spinnerets recede at the rear left, not on the near flank.
        oval(-66,119,4,3,SHELL_DARK,INK,1.1,angle=32)

    with c.part('quarter_carapace',(cx+14,122),key=('quarter','carapace')):
        shape([(-20,116),(-19,103),(-4,96),(12,98),
               (30,98),(43,111),(46,124),
               (51,138),(37,149),(20,151),
               (0,153),(-19,140),(-20,116)],SHELL,INK,2.4)
        shape([(-15,115),(-11,103),(6,100),(20,105),
               (30,107),(34,112),(36,118),
               (17,111),(4,110),(-4,119),
               (-9,124),(-13,119),(-15,115)],SHELL_LIGHT,None)
        shape([(-17,130),(-9,139),(1,143),(13,144),
               (24,147),(37,143),(45,136),
               (41,148),(21,151),(7,148),
               (-6,147),(-14,140),(-17,130)],SHELL_DARK,None)
        line([(-15,124),(-6,133),(2,136),(14,138)],SHELL_DARK,1.6)
        for x,y in [(-10,108),(-5,103),(4,102),(13,103),(22,106),(-14,117)]:
            line([(x,y),(x-2,y-2.5)],HAIR,.85)

    # Foreground legs overlay the lower lateral plate. Their frontmost
    # root stays below the eye bank, so the face is never erased by a knee.
    for k in (3,2,1,0):
        _leg_chain(c,f'quarter_near_{k}',*(P(*v) for v in near_legs[k]),True,
                   1 if k<2 else -1)
    with c.part('quarter_eye_plate',(cx+27,126),key=('quarter','eyes')):
        shape([(9,117),(17,109),(31,111),(37,114),
               (44,118),(47,124),(46,130),
               (48,139),(38,142),(28,141),
               (18,143),(8,133),(9,117)],'#36282a',None)
        # Two principal forward eyes, six smaller eyes; the eye bank
        # wraps around the convex plate instead of looking like two rows
        # pasted onto a flat surface.
        eyes = [(23,126,5.3,4.8),(39,125,4.1,3.8),
                (13,119,2.5,2.3),(21,114,2.8,2.4),
                (32,115,2.5,2.3),(42,118,2.1,2.0),
                (14,133,2.2,2.0),(33,136,2.0,1.8)]
        for x,y,rx,ry in eyes:
            oval(x,y,rx,ry,'#211a21',INK,1.0)
            oval(x+.25,y,rx*.73,ry*.74,EYE,None)
            if rx>3:
                oval(x+.6,y+.25,rx*.29,ry*.61,'#35222a',None)
            oval(x-.8,y-1.,rx*.21,ry*.21,'#f7d19c',None)
    # The farther chelicera emerges behind the near one. Both fangs are
    # curved towards the centre of the mouth, visible below the eye bank.
    with c.part('quarter_chelicera_far',(cx+41,145),key=('quarter','fang_far')):
        oval(46,140,4.1,5.0,FAR_LEG,INK,1.1,angle=-25)
        shape([(38,136),(42,132),(48,137),(49,141),
               (51,146),(46,151),(42,150),
               (38,149),(36,141),(38,136)],FAR_LEG,INK,1.4)
        shape([(44,147),(47,146),(49,150),(48,154),
               (46,159),(41,161),(38,160),
               (43,156),(44,151),(44,147)],'#9b806c',INK,1.25)
    with c.part('quarter_chelicera_near',(cx+26,146),key=('quarter','fang_near')):
        oval(15,141,5.3,6.1,LEG_DARK,INK,1.1,angle=20)
        shape([(23,137),(28,134),(33,137),(34,143),
               (36,149),(31,154),(27,153),
               (22,153),(20,143),(23,137)],SHELL_DARK,INK,1.5)
        shape([(27,150),(31,148),(35,153),(34,157),
               (32,164),(27,167),(23,165),
               (28,161),(30,155),(27,150)],FANG,INK,1.3)
        line([(31,152),(31,157),(28,162)],'#e0bfa4',.9)
    return c.finish()


def _reflect(frame):
    """Mirror around the collision anchor, not the padded canvas center."""
    out = Image.new('RGBA', FRAME_SIZE)
    rigdoc.composite_canvas(out, rigdoc.mirrored_canvas(frame),
                            (BODY_BOX[0]+BODY_BOX[2]-FRAME_SIZE[0],0))
    return out


def _render_frame(anim, i, n):
    if anim == 'turnaround':
        assert n == 5
        if i == 2:
            return _front_frame()
        im = _quarter_frame() if i in (1,3) else _render_side_frame('idle',0,12)
        return _reflect(im) if i < 2 else im
    return _render_side_frame(anim, i, n)


def render(out_dir: str | Path, **opts):
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True,exist_ok=True)
    transform = {}
    out = build_sheet(
        target=TARGET_NAME, rows=ROWS, render_fn=_render_frame,
        out_dir=out_dir, frame_size=FRAME_SIZE, auto_crop=False,
        actor_metadata=ACTOR_METADATA,
        body_metrics_fn=lambda w,h: body_metrics_for_box(BODY_BOX,w,h),
        animation_key_map={name:name for name,_,_ in ROWS},
        pose_bodies='authored', sits_on_ground=True,
        parts=True, frame_transform_out=transform,
    )
    parts = publish_rig_flipbook(TARGET_NAME,ROWS,_render_frame,out,transform,out_dir)
    return [out[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')
            if out.get(k)] + list(parts.values())
