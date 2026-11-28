"""Part-first rat family: locally painted anatomical pieces and authored yaw views."""
from __future__ import annotations

import math
from contextlib import contextmanager
from PIL import Image
import numpy as np
from ._magic_character_art import Canvas, add, sub, mul, mix, unit, perp, rot, bezier
from ...authoring import rigdoc

class PartScene:
    """Record reusable local rasters, in the same order as the preview paint.

    Joint targets are calculated in world pixels. Segment length changes use
    local-axis scaling; no full character image is ever used as a part.
    """
    _cache = {}
    s = 3
    # Enough space to draw an entire anatomical part about its local pivot.
    local_size = (512, 360)
    center = (256, 170)

    def __init__(self, module):
        self.module = module
        self.ops = []
        self.local = None
        self.anchor = None
        self.cached = False

    @contextmanager
    def part(self, name, anchor=(0.,0.), *, key=None, at=None,
             degrees=0., scale_y=1.):
        assert self.anchor is None, name
        self.anchor = anchor
        key = (self.module.TARGET_NAME, key) if key is not None else None
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

    def poly(self, pts, color, edge="#292327", w=1.8):
        if not self.cached:
            self.local.poly([self._pt(v) for v in pts], color, edge, w)

    def line(self, pts, color, w=1.5):
        if not self.cached:
            self.local.line([self._pt(v) for v in pts], color, w)

    def oval(self, p, rx, ry, fill, edge="#292327", w=1.5, angle=0):
        if not self.cached:
            self.local.oval(self._pt(p),rx,ry,fill,edge,w,angle)

    def disk(self, p, r, fill, edge="#292327", w=1.5):
        self.oval(p,r,r,fill,edge,w)

    def finish(self, ground_lock=False):
        frame = Image.new('RGBA', tuple(v*self.s for v in self.module.FRAME_SIZE))
        dy = 0
        if ground_lock:
            bottom = -math.inf
            for _,im,pivot,at,deg,sy in self.ops:
                yy,xx = np.nonzero(np.asarray(im.getchannel('A'))>=32)
                if len(yy):
                    r = math.radians(deg)
                    support = (xx-pivot[0])*math.sin(r)+(yy-pivot[1])*sy*math.cos(r)
                    bottom = max(bottom, at[1]+float(support.max())+1)
            dy = round((self.module.GROUND+1)*self.s-bottom)
        for name,im,pivot,at,deg,sy in self.ops:
            rigdoc.blit_rotated(frame,im,pivot,(at[0],at[1]+dy),deg,
                                part_name=name,scale_y=sy)
        return rigdoc.downsampled_canvas(frame,self.module.FRAME_SIZE,Image.Resampling.LANCZOS)



def limb_segment(c, name, a, b, ra, rb, col, light, edge):
    """Soft fur contour in local bone coordinates; overlap at the elbow.

    Discrete lengths share rasters across gait samples, while independent
    rotations and longitudinal scales land the joints at their targets.
    No hard discs or cross-seam outlines are drawn at the joints.
    """
    dx,dy=sub(b,a)
    length=max(.5,math.hypot(dx,dy))
    L=max(4,4*round(length/4))
    angle=math.degrees(math.atan2(-dx,dy))
    with c.part(name,key=('bone',ra,rb,col,L),at=a,degrees=angle,scale_y=length/L):
        # Both sides of the taper extend into the adjacent segment.
        top=-min(ra*.50,L*.20); bottom=L+min(rb*.48,L*.18)
        left=bezier((-ra*.70,top),(-ra*1.06,L*.22),(-rb*1.03,L*.72),(-rb*.77,bottom),n=12)
        right=bezier((ra*.70,top),(ra*1.06,L*.22),(rb*1.03,L*.72),(rb*.77,bottom),n=12)
        c.poly(left+right[::-1],col,None)
        c.line(left[1:-1],edge,1.25)
        c.line(right[1:-1],edge,1.25)
        c.line([mix(x,y,.28) for x,y in zip(left,right)][3:-3],light,1.1)


def reflect(module, frame):
    out=Image.new('RGBA',module.FRAME_SIZE)
    rigdoc.composite_canvas(out,rigdoc.mirrored_canvas(frame),
                           (module.BODY_BOX[0]+module.BODY_BOX[2]-module.FRAME_SIZE[0],0))
    return out


def quarter_frame(m):
    """Draw a yawed rat from independent anatomical landmarks.

    The rump recedes left and up; the shoulders are nearer, and the muzzle
    projects right and down. Both eyes are drawn on the curved skull.
    The four feet occupy different depth rows on the ground plane.
    """
    c=PartScene(m)
    plague=m.TARGET_NAME=='plague_rat'
    cx=(m.BODY_BOX[0]+m.BODY_BOX[2]-1)/2
    sx,sy=(1.35,1.46) if plague else (1.,1.)
    giant=not plague
    # All landmarks are authored in the quarter view; this is not a warp
    # of the side image. The two species share the perspective convention.
    def P(x,y):return (cx+x*sx,m.GROUND+y*sy)
    def shape(pts,col,edge=m.INK,w=1.8):m._shape(c,[P(*v) for v in pts],col,edge,w)
    def poly(pts,col,edge=m.INK,w=1.4):c.poly([P(*v) for v in pts],col,edge,w)
    def line(pts,col,w=1.1):c.line([P(*v) for v in pts],col,w)
    def oval(x,y,rx,ry,col,edge=m.INK,w=1.4,angle=0):c.oval(P(x,y),rx*sx,ry*sy,col,edge,w,angle)
    # The tail emerges from the left rear of the rump, at a receding angle.
    with c.part('quarter_tail',P(-45,-30),key=('quarter','tail')):
        tail=m._curve([P(-44,-30),P(-65,-13),P(-88,-7),P(-100,-16),
                       P(-110,-24),P(-107,-33),P(-105,-32)])
        left,right=[],[]
        for j,p in enumerate(tail):
            f=j/(len(tail)-1)
            normal=perp(unit(sub(tail[min(j+1,len(tail)-1)],tail[max(j-1,0)])))
            r=(5.4 if plague else 4.6)*sx*(1-f)**.80+.7*sx
            left.append(add(p,mul(normal,r)));right.append(add(p,mul(normal,-r)))
        c.poly(left+right[::-1],m.TAIL,m.INK,1.6)
        c.line([mix(a,b,.28) for a,b in zip(left,right)],m.SKIN_LIGHT,1.1)
        for j in range(2,len(tail)-1,2):
            c.line([mix(left[j],right[j],.09),mix(left[j],right[j],.92)],m.SKIN_DARK,.9)
        if plague:
            c.poly([left[10],left[14],mix(left[15],right[15],.65),mix(left[11],right[11],.65)],'#73645a',None)

    def leg(label,front,near,hip,knee,ankle,foot):
        col,light,edge=(m.FUR,m.FUR_LIGHT,m.INK) if near else (m.FAR,m.FAR_LIGHT,m.FAR_INK)
        skin,sl=(m.SKIN,m.SKIN_LIGHT) if near else (m.SKIN_DARK,m.SKIN)
        # Four independently authored quarter-view limb chains, feet not
        # translated copies: the forefeet point toward the camera and right.
        widths=(8.7,5,3.0) if front else (12.0,7.5,3.2)
        if plague: widths=tuple(v*1.42 for v in widths)
        if not near: widths=tuple(v*.79 for v in widths)
        x,y=foot
        with c.part('quarter_'+label+'_paw',P(x,y),key=('quarter','paw',label)):
            shape([(x-5,y-3),(x-1,y-5),(x+5,y-3),(x+8,y),
                   (x+12,y+2),(x+12,y+4),(x+6,y+5),
                   (x+1,y+5),(x-6,y+3),(x-5,y-3)],skin,edge,1.35)
            for k in range(3):
                px=x+2+k*3
                line([(px-1,y+1),(px,y+3)],m.SKIN_DARK,.75)
                poly([(px-1,y+3),(px+2,y+3),(px+1,y+5.6)],m.TOOTH,edge,.65)
        limb_segment(c,'quarter_'+label+'_wrist',P(*ankle),P(*foot),widths[2],widths[2]*.72,skin,sl,edge)
        limb_segment(c,'quarter_'+label+'_lower',P(*knee),P(*ankle),widths[1],widths[2],col,light,edge)
        limb_segment(c,'quarter_'+label+'_upper',P(*hip),P(*knee),widths[0],widths[1],col,light,edge)
    # The far feet are higher on the image; both chains are behind torso.
    if plague:
        leg('far_hind',False,False,(-31,-40),(-27,-30),(-38,-16),(-39,-13))
        leg('far_fore',True,False,(21,-38),(33,-25),(39,-12),(42,-9))
    else:
        leg('far_hind',False,False,(-33,-41),(-29,-31),(-40,-17),(-41,-14))
        leg('far_fore',True,False,(19,-40),(30,-27),(37,-13),(40,-10))

    with c.part('quarter_torso',P(-18,-45),key=('quarter','torso')):
        # Visible haunch is on the canvas left, near shoulder on the right.
        top=-91 if plague else -83
        shape([(-52,-38),(-64,-57),(-53,top+11),(-32,top+5),
               (-16,top-2),(-1,top+12),(11,top+15),
               (26,-64),(35,-55),(34,-42),
               (44,-25),(24,-15),(6,-14),
               (-18,-8),(-45,-17),(-52,-38)],m.FUR,m.INK,2.5)
        shape([(-53,-55),(-50,top+14),(-38,top+5),(-23,top+8),
               (-8,top+7),(9,top+20),(17,-60),
               (2,-65),(-21,-64),(-31,-60),
               (-41,-55),(-48,-48),(-53,-55)],m.FUR_LIGHT,None)
        shape([(-48,-30),(-33,-19),(-13,-18),(1,-20),
               (17,-20),(30,-29),(34,-37),
               (35,-24),(19,-15),(0,-14),
               (-19,-12),(-40,-17),(-48,-30)],m.BELLY,None)
        back=[(-49,-64),(-40,top+10),(-28,top+5),(-16,top+7),(-5,top+13),(7,top+18),(19,-64)]
        for j,(x,y) in enumerate(back):
            h=(7+(j%3)*2) if plague else (3.4+j%2)
            poly([(x-5,y+4),(x-3,y-h),(x+1,y-1),(x+5,y+4)],m.FUR_DARK,None)
        for x,y in [(-46,-54),(-35,-62),(-22,-63),(-11,-56),(-2,-52),(-43,-39),(-29,-35),(-15,-31),(-3,-28)]:
            line([(x,y),(x+6,y+3)],m.FUR_DARK,1.3 if plague else 1.05)
            line([(x+1,y-2),(x+5,y)],m.FUR_LIGHT,.8)
        if plague:
            shape([(-43,-42),(-44,-52),(-33,-53),(-29,-47),(-23,-39),(-34,-34),(-43,-42)],'#786960',m.FUR_DARK,1.1)
            for x,y in [(-38,-46),(-34,-42),(-38,-38)]:oval(x,y,1.5,1.0,'#9b8872',None)
            for x,y in [(-43,-26),(-30,-19),(-19,-16),(-5,-15)]:
                poly([(x-6,y-2),(x+1,y+7),(x+4,y+1),(x+7,y-4)],m.FUR_DARK,None)

    # Near haunch and shoulder overlap the barrel. The near forepaw is
    # lower and more central than the far one, avoiding the face silhouette.
    if plague:
        leg('near_hind',False,True,(-30,-37),(-19,-30),(-30,-9),(-28,-6))
        leg('near_fore',True,True,(11,-35),(16,-22),(13,-8),(14,-6))
    else:
        leg('near_hind',False,True,(-29,-38),(-17,-30),(-28,-10),(-25,-6))
        leg('near_fore',True,True,(12,-36),(18,-23),(16,-9),(18,-5))

    # Small far ear follows the far side of the skull, ahead of the hump.
    def ear(far):
        if plague:
            x,y=(23,-73) if far else (-3,-77)
        else:
            x,y=(21,-72) if far else (-6,-79)
        # Smaller far ear is partially occluded by the skull; the large
        # near pinna has the original notch (larger missing wedge on plague).
        sc=.72 if far else 1.
        def E(a,b):return (x+a*sc,y+b*sc)
        def S(seq,col,edge=m.INK,w=1.6):shape([E(*v) for v in seq],col,edge,w)
        with c.part('quarter_'+('far' if far else 'near')+'_ear',P(x,y),key=('quarter','ear',far)):
            rim=[(-9,9),(-16,-4),(-14,-16),(-5,-19),(5,-22),(14,-16),(13,-8),
                 (8,-10),(8,-5),(12,-3),(10,6),(1,12),(-9,9)]
            if plague and not far:
                rim=[(-9,9),(-16,-4),(-14,-16),(-7,-20),(-5,-21),(-3,-21),(-2,-19),
                     (-5,-15),(-8,-9),(-5,-8),(-1,-10),(1,-17),(3,-17),
                     (11,-16),(14,-10),(13,-4),(11,5),(1,12),(-9,9)]
            S(rim,m.FAR if far else m.FUR,m.FAR_INK if far else m.INK,1.75)
            S([(-6,6),(-11,-3),(-9,-14),(-3,-15),(5,-17),(9,-10),(8,-4),
               (6,3),(1,8),(-6,6)],m.SKIN_DARK if far else m.SKIN,None)
            S([(-4,6),(-7,-1),(-3,-8),(1,-10),(-1,-1),(2,2),(4,4),(1,8),(-2,8),(-4,6)],m.FUR_DARK,None)
            line([E(-8,-10),E(-3,-14),E(2,-14)],m.SKIN_LIGHT,1.)
    ear(True)
    with c.part('quarter_jaw',P(22,-36),key=('quarter','jaw')):
        if plague:
            shape([(9,-44),(20,-48),(39,-41),(48,-37),
                   (55,-33),(51,-26),(40,-26),
                   (25,-21),(13,-28),(9,-44)],m.FUR_PALE,m.INK,1.8)
        else:
            shape([(9,-44),(20,-49),(36,-43),(46,-39),
                   (52,-34),(48,-28),(39,-28),
                   (24,-22),(13,-29),(9,-44)],m.FUR_PALE,m.INK,1.8)
        if plague:
            shape([(22,-38),(31,-38),(46,-37),(49,-33),(45,-26),(30,-27),(22,-30)],'#362d28',None)
        # Paired incisors visible under the oblique muzzle.
        tooth_end=-22 if plague else -25
        poly([(40,-37),(45,-37),(44,tooth_end),(39,tooth_end-1)],m.TOOTH,m.INK,1.0)
        poly([(45,-37),(49,-38),(49,tooth_end-3),(44,tooth_end-1)],m.TOOTH if not plague else '#b39a60',m.INK,1.0)
    with c.part('quarter_skull',P(11,-55),key=('quarter','skull')):
        # Broad cheek nearer the viewer and a small far brow wrapping around
        # the muzzle. A curved skull and projecting rostrum replace a flat
        # frontal mask. The nose lies forward and lower than either eye.
        if plague:
            shape([(-15,-64),(-11,-78),(7,-84),(22,-76),
                   (35,-75),(37,-64),(40,-58),
                   (42,-51),(55,-47),(58,-41),
                   (61,-36),(54,-32),(45,-34),
                   (35,-32),(29,-28),(20,-29),
                   (6,-26),(-11,-34),(-15,-49),
                   (-19,-54),(-16,-61),(-15,-64)],m.FUR,m.INK,2.35)
            shape([(-9,-62),(-4,-76),(9,-79),(20,-73),
                   (30,-73),(33,-67),(34,-62),
                   (24,-67),(15,-69),(7,-65),
                   (-2,-59),(-7,-57),(-9,-62)],m.FUR_LIGHT,None)
            shape([(11,-44),(20,-49),(34,-47),(42,-44),
                   (52,-42),(57,-39),(53,-36),
                   (43,-34),(34,-31),(24,-31),
                   (17,-33),(12,-37),(11,-44)],m.FUR_PALE,None)
            # A darker near cheek and smaller far muzzle plane create yaw depth.
            shape([(-8,-43),(-3,-36),(4,-34),(11,-34),
                   (15,-29),(7,-28),(-1,-30),
                   (-9,-34),(-10,-39),(-8,-43)],m.FUR_DARK,None)
            shape([(34,-56),(40,-54),(46,-48),(51,-45),
                   (47,-44),(41,-45),(35,-48),
                   (32,-51),(32,-54),(34,-56)],m.FUR_LIGHT,None)
        else:
            shape([(-15,-65),(-10,-79),(6,-84),(19,-78),
                   (31,-77),(35,-69),(37,-61),
                   (39,-54),(50,-49),(54,-43),
                   (56,-38),(50,-34),(42,-35),
                   (33,-33),(28,-29),(19,-29),
                   (5,-27),(-9,-35),(-14,-49),
                   (-18,-55),(-16,-61),(-15,-65)],m.FUR,m.INK,2.35)
            shape([(-9,-63),(-4,-76),(8,-79),(18,-75),
                   (28,-74),(31,-68),(32,-63),
                   (23,-68),(14,-69),(6,-65),
                   (-2,-60),(-7,-58),(-9,-63)],m.FUR_LIGHT,None)
            shape([(10,-45),(18,-49),(31,-47),(39,-45),
                   (47,-43),(52,-40),(49,-37),
                   (40,-35),(31,-32),(22,-32),
                   (16,-34),(11,-38),(10,-45)],m.FUR_PALE,None)
            # Broader near cheek and shorter far muzzle for cleaner giant-rat depth.
            shape([(-8,-43),(-2,-36),(5,-34),(13,-34),
                   (16,-30),(8,-28),(-1,-30),
                   (-9,-34),(-10,-39),(-8,-43)],m.FUR_DARK,None)
            shape([(31,-56),(37,-54),(43,-49),(48,-45),
                   (44,-44),(38,-45),(33,-48),
                   (30,-51),(29,-54),(31,-56)],m.FUR_LIGHT,None)
    ear(False)
    with c.part('quarter_face',P(25,-53),key=('quarter','face')):
        # Far eye is narrower and higher; near eye is larger and set into
        # the cheek plane. Both have the same iris color and slit pupil.
        for x,y,rx,ry in ([(15,-60,5.5,4.2),(34,-60,3.3,3.0)] if plague else [(13,-60,5.8,4.3),(31,-60,3.1,2.9)]):
            poly([(x-rx-2,y-ry),(x+rx+1,y-ry+2),(x+rx,y+ry),(x-rx,y+ry)],m.FUR_DARK,m.INK,1.15)
            oval(x,y,rx*.74,ry*(.62 if plague else .78),m.EYE,None)
            oval(x+.7,y,rx*.23,ry*(.50 if plague else .60),'#211d21',None)
            oval(x-.9,y-1.15,.85,.9,'#f8e8c7',None)
            if plague:
                # The heavy oblique brow cuts across the upper iris. The
                # far brow slopes oppositely around the skull's far plane.
                slope=1 if x<25 else -1
                poly([(x-rx-2,y-ry-3*slope-2),(x+rx+1,y-ry+2*slope),
                      (x+rx+1,y-ry+2*slope+2),(x-rx-2,y-ry-3*slope+2)],m.FUR_DARK,None)
                line([(x-rx-3,y-ry-2*slope-2),(x+rx+2,y-ry+2*slope)],m.FUR_DARK,3.3)
            else:
                line([(x-rx-3,y-ry-2),(x-1,y-ry-3),(x+rx+2,y-ry+1)],m.FUR_DARK,2.3)
        # The nose and whisker roots lie forward of both eyes, on the
        # rounded muzzle rather than centered on the head silhouette.
        for x,y in ([(37,-42),(42,-40),(39,-36),(48,-39)] if plague else [(34,-42),(39,-40),(36,-36),(45,-39)]):
            oval(x,y,.85,.85,m.FUR_DARK,None)
        for pts in ([[(40,-42),(57,-47),(71,-51)],[(43,-40),(62,-40),(77,-38)],
                    [(40,-37),(55,-31),(69,-26)],[(36,-35),(46,-27),(55,-22)],
                    [(49,-42),(60,-47),(68,-47)]] if plague else
                    [[(37,-42),(53,-47),(66,-51)],[(40,-40),(58,-40),(71,-38)],
                     [(37,-37),(52,-31),(65,-26)],[(34,-35),(44,-27),(53,-22)],
                     [(46,-42),(56,-47),(63,-47)]]):
            line(pts,'#62534b',1.05)
            line(pts[:2],'#d0b9a1',.65)
        nose_x = 55 if plague else 52
        oval(nose_x,-39,5.7 if plague else 5.2,4.3 if plague else 3.9,m.SKIN_DARK,m.INK,1.4,angle=-13)
        oval(nose_x,-41,2.0,1.0,m.SKIN_LIGHT,None)
        line([(nose_x-3,-36),(nose_x-5,-33)],m.INK,1.0)
        if plague:
            line([(3,-47),(7,-42),(10,-36)],m.SKIN,1.8)
            line([(4,-45),(7,-42)],m.FUR_DARK,.9)
            line([(31,-49),(37,-51),(42,-48)],m.FUR_DARK,1.35)
            line([(42,-29),(41,-24),(40,-20)],m.SICK,1.7)
            oval(40,-19.5,1.6,2.0,m.SICK,m.INK,.6)
    return c.finish()
