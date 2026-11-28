"""Local anatomical parts and joint placement for the imp family.

The side rigs keep their original joint trajectories. A finite set of local
wing, tail and expression shapes handles organic deformation. Draw transforms
carry the body pitch, joint angles and bone lengths, not unique frame images.
"""
from __future__ import annotations

import math
from contextlib import contextmanager
from PIL import Image

from ._magic_character_art import Canvas, add, sub, rot, bezier, mix
from ...authoring import rigdoc


def quant(value, step):
    return round(value / step) * step


class ImpScene:
    _cache = {}
    s = 3
    center = (220, 190)
    local_size = (440, 380)

    def __init__(self, target, size, origin, pitch=0.):
        self.target, self.size, self.origin, self.pitch = target, size, origin, pitch
        self.ops = []
        self.local = None
        self.anchor = None
        self.cached = False

    @contextmanager
    def part(self, name, anchor=(0., 0.), *, key=None, at=None,
             degrees=0., scale_y=1.):
        assert self.anchor is None, name
        self.anchor = anchor
        key = (self.target, name, key) if key is not None else None
        raster = self._cache.get(key) if key is not None else None
        self.cached = raster is not None
        self.local = None if self.cached else Canvas(self.local_size, self.s)
        try:
            yield
            if raster is None:
                im = self.local.image
                box = im.getbbox()
                if box is None:
                    return
                x0, y0, x1, y1 = box
                assert x0 > 6 and y0 > 6 and x1 < im.width-6 and y1 < im.height-6, name
                x0 = (x0-6)//self.s*self.s
                y0 = (y0-6)//self.s*self.s
                x1 = math.ceil((x1+6)/self.s)*self.s
                y1 = math.ceil((y1+6)/self.s)*self.s
                pivot = (self.center[0]*self.s-x0, self.center[1]*self.s-y0)
                raster = (im.crop((x0,y0,x1,y1)), pivot)
                if key is not None:
                    self._cache[key] = raster
            dest = add(self.origin, rot(anchor if at is None else at, self.pitch))
            self.ops.append((name, *raster, tuple(round(v*self.s) for v in dest),
                             degrees+self.pitch, scale_y))
        finally:
            self.local = self.anchor = None
            self.cached = False

    def _pt(self, p):
        return add(sub(p, self.anchor), self.center)

    def poly(self, pts, color, edge, w):
        if not self.cached:
            self.local.poly([self._pt(p) for p in pts], color, edge, w)

    def line(self, pts, color, w):
        if not self.cached:
            self.local.line([self._pt(p) for p in pts], color, w)

    def oval(self, p, rx, ry, color, edge, w, angle=0.):
        if not self.cached:
            self.local.oval(self._pt(p), rx, ry, color, edge, w, angle)

    def finish(self, opacity=1.):
        canvas = Image.new('RGBA', tuple(v*self.s for v in self.size))
        for name, im, pivot, at, deg, sy in self.ops:
            rigdoc.blit_rotated(canvas, im, pivot, at, deg, part_name=name, scale_y=sy)
        frame = rigdoc.downsampled_canvas(canvas, self.size, Image.Resampling.LANCZOS)
        return rigdoc.faded_canvas(frame, opacity) if opacity < 1. else frame


def bone(c, name, a, b, ra, rb, color, light, edge, *, bulk=1.):
    """Overlapping soft contours. A local-axis scale lands the distal joint."""
    dx,dy=sub(b,a)
    length=max(.5,math.hypot(dx,dy))
    # A stable rest length per anatomical track avoids per-sample textures.
    L=max(8., 3.2*(ra+rb))
    angle=math.degrees(math.atan2(-dx,dy))
    with c.part(name,key=(ra,rb,color,light,bulk),at=a,degrees=angle,scale_y=length/L):
        # Slight overlap hides the joint end cap beneath the proximal piece.
        top=-min(ra*.62,L*.19); bottom=L+min(rb*.66,L*.22)
        left=bezier((-ra*.68,top),(-ra*bulk,L*.23),(-rb*1.03,L*.73),(-rb*.83,bottom),n=14)
        right=bezier((ra*.68,top),(ra*bulk,L*.23),(rb*1.03,L*.73),(rb*.83,bottom),n=14)
        c.poly(left+right[::-1],color,None,1.)
        c.line(left[1:-1],edge,max(1.3,ra*.19))
        c.line(right[1:-1],edge,max(1.3,ra*.19))
        if light:
            c.line([mix(x,y,.26) for x,y in zip(left,right)][2:-3],light,max(.8,ra*.18))


def chain(c, name, joints, widths, color, light, edge, bulk=1.):
    # Distal first so the upper muscle overlaps the elbow or knee seam.
    a,b,d=joints
    ra,rb,rd=widths
    bone(c,name+'_lower',b,d,rb,rd,color,light,edge,bulk=1.12)
    bone(c,name+'_upper',a,b,ra,rb,color,light,edge,bulk=bulk)


def reflect(frame, box):
    out=Image.new('RGBA',frame.size)
    rigdoc.composite_canvas(out,rigdoc.mirrored_canvas(frame),
                           (box[0]+box[2]-frame.width,0))
    return out


def turn_frame(i,n,idle,front,quarter,box):
    assert n==5
    if i==2:
        return front()
    frame=quarter() if i in (1,3) else idle()
    return reflect(frame,box) if i<2 else frame


# Parent-relative interpolation keeps a child's pivot on its carrying limb.
# The authored front and quarter views step; the side tracks can be tweened.
TRACK_PARENTS = {'head': 'torso', 'face': 'head', 'tail': 'torso'}
for side in ('near', 'far'):
    TRACK_PARENTS[side+'_wing'] = 'torso'
    for limb, end in (('arm', 'hand'), ('leg', 'foot')):
        prefix=side+'_'+limb
        TRACK_PARENTS[prefix+'_upper']='torso'
        TRACK_PARENTS[prefix+'_lower']=prefix+'_upper'
        TRACK_PARENTS[prefix+'_'+end]=prefix+'_lower'
