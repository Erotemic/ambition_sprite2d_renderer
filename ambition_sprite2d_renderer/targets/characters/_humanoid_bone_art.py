"""Paint a humanoid skeleton from solved joints, without clothing or weapons.

The caller owns proportions, pose, frame size, and effect timing. Draw far
limbs, the trunk, skull, and near limbs in that order. The same painters can
also draw a bright bone layer for a damage effect. No runtime effect contract
is defined here.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from ._clockwork_enemy_art import add, sub, mul, mix, norm, unit, perp, rot, bezier

Point = tuple[float, float]


@dataclass(frozen=True)
class BonePalette:
    ink: str = '#39332d'
    bone: str = '#d9cbae'
    light: str = '#f4e9cc'
    shade: str = '#95846b'
    cavity: str = '#423a32'


IVORY = BonePalette()
FLASH = BonePalette('#173d63', '#e6faff', '#ffffff', '#80c9f5', '#193a59')


def _colors(palette, far):
    return ((palette.shade, palette.bone, palette.cavity) if far else
            (palette.bone, palette.light, palette.shade))


def long_bone(c, a, b, width, palette=IVORY, far=False):
    """Draw a tapered shaft with wider joint ends between two points."""
    v = sub(b, a)
    length = norm(v)
    if length < 1e-5:
        return
    u, n = unit(v), perp(unit(v))
    base, light, shade = _colors(palette, far)

    def p(t, r):
        return add(add(a, mul(u, length*t)), mul(n, width*r))

    c.poly([p(0,-.75), p(.05,-1), p(.14,-.90), p(.25,-.48),
            p(.74,-.43), p(.88,-.88), p(.98,-1), p(1.04,-.50),
            p(1.04,.53), p(.98,.98), p(.88,.82), p(.73,.50),
            p(.25,.53), p(.12,.88), p(.03,.93), p(-.045,.40)],
           base, palette.ink, .95)
    c.line([p(.10,-.52), p(.25,-.22), p(.72,-.21), p(.91,-.54)], light, .95)
    c.line([p(.26,.36), p(.72,.33), p(.88,.57)], shade, .9)


def paired_bones(c, a, b, width, palette=IVORY, far=False):
    """Draw the two bones of a forearm or lower leg with a gap between them."""
    n = perp(unit(sub(b, a)))
    long_bone(c, add(a,mul(n,-width*.52)), add(b,mul(n,-width*.40)),
              width*.57, palette, far)
    long_bone(c, add(a,mul(n,width*.58)), add(b,mul(n,width*.56)),
              width*.39, palette, far)


def hand(c, wrist, angle, scale=1., palette=IVORY, far=False, grip=False):
    base, light, _ = _colors(palette, far)
    def p(x,y): return add(wrist,rot((x*scale,y*scale),angle))
    c.oval(p(2.3,0), 4.1*scale, 3.3*scale, base, palette.ink, .85*scale, angle)
    for j, length in enumerate((7.7, 9.0, 8.2, 6.5)):
        y = -2.6+j*1.65
        tip = (length-1.5, y+1.7) if grip else (length+1.,y+1.)
        c.line([p(3,y),p(length*.72,y),p(*tip)], palette.ink, 2.25*scale)
        c.line([p(3,y),p(length*.72,y),p(*tip)], light, 1.15*scale)
    c.line([p(0,2),p(3.6,5),p(5.4,3.6)], palette.ink, 2.4*scale)
    c.line([p(0,2),p(3.6,5),p(5.4,3.6)], base, 1.3*scale)


def foot(c, ankle, angle=0., scale=1., palette=IVORY, far=False):
    base, light, shade = _colors(palette, far)
    def p(x,y): return add(ankle,rot((x*scale,y*scale),angle))
    c.poly([p(-4,1),p(-2,-2),p(2,-2),p(6,0),p(10,1),p(11,3),p(-3,3)],
           base,palette.ink,.95*scale)
    for y,x in ((-.4,12), (1.0,11.5), (2.4,10.3)):
        c.line([p(4,y),p(x,y+.2)],shade,1.0*scale)
        c.line([p(5,y-.5),p(x-1,y-.3)],light,.7*scale)


def skull(c, center, tilt=0., scale=1., jaw=0., palette=IVORY, eye=None):
    """Draw a right-facing three-quarter skull. Eye light is optional."""
    p = palette
    def h(x,y): return add(center,rot((x*scale,y*scale),tilt))
    def poly(points,col,edge=None,w=1.): c.poly([h(*a) for a in points],col,edge,w*scale)
    def line(points,col,w=1.): c.line([h(*a) for a in points],col,w*scale)
    # Separate mandible behind the upper teeth.
    poly([(-10,5),(-7,13+jaw),(2,17+jaw),(11,15+jaw),(13,10+jaw),
          (9,8+jaw),(7,12+jaw),(1,13+jaw),(-4,10+jaw),(-5,4)],p.bone,p.ink,1.2)
    poly([(-8,8),(-5,13+jaw),(3,16+jaw),(10,14+jaw),(7,12+jaw),(0,13+jaw)],p.shade)
    # Cranial vault, cheekbone, nasal bridge, maxilla.
    poly([(-13,-11),(-9,-16),(-2,-18),(7,-17),(13,-12),(15,-6),
          (14,-1),(16,3),(13,5),(13,9),(8,11),(-1,10),(-3,6),
          (-8,6),(-12,2),(-15,-3)],p.bone,p.ink,1.3)
    poly([(-14,-8),(-11,-2),(-6,2),(-9,6),(-12,2),(-15,-3)],p.shade)
    poly([(-9,-13),(-2,-16),(6,-15),(10,-12),(4,-13),(-4,-12)],p.light)
    poly([(-6,-6),(0,-8),(6,-5),(5,0),(1,3),(-4,1),(-7,-2)],p.cavity)
    poly([(9,-6),(13,-5),(14,-2),(12,1),(9,0),(8,-3)],p.cavity)
    poly([(7,0),(10,4),(6,5),(5,3)],p.cavity)
    if eye:
        c.oval(h(0,-2),1.8*scale,1.7*scale,eye,None,0,tilt)
    line([(-8,-7),(-2,-9),(5,-7)],p.light,1.5)
    line([(-5,3),(0,4),(4,2)],p.light,1.2)
    line([(-1,7),(12,7)],p.shade,1.1)
    for x in (1,4,7,10):
        line([(x,7),(x,10)],p.cavity,.8)
        line([(x,12+jaw),(x,14+jaw)],p.shade,.75)
    line([(-7,-15),(-5,-12),(-7,-10)],p.shade,.75)


def trunk(c, pelvis, neck, palette=IVORY):
    """Draw vertebrae, open ribs, clavicles, and pelvis along the trunk axis."""
    up = unit(sub(neck,pelvis)); right = (-up[1],up[0])
    scale = norm(sub(neck,pelvis))/43.
    if scale < .01:
        return
    p = palette
    def q(x,y): return add(pelvis,add(mul(right,x*scale),mul(up,y*scale)))
    def poly(points,col,edge=None,w=1.): c.poly([q(*a) for a in points],col,edge,w*scale)
    def line(points,col,w=1.): c.line([q(*a) for a in points],col,w*scale)
    # Far side ribs: leave visible gaps, not a solid plate.
    for j in range(6):
        y=34-j*4.15; radius=(9,11,12,12,10.5,8)[j]
        pts=bezier(q(-2,y),q(-radius-3,y-1),q(-radius-2,y-7),q(2,y-6),n=10)
        c.line(pts,p.ink,3.5*scale); c.line(pts,p.shade,2.1*scale)
    # Individual vertebrae and a narrow spinal column.
    line([(-1,3),(-3,18),(-3,30),(-1,42)],p.ink,5.0)
    for j in range(10):
        y=5+j*3.6; x=-2.7 if j<8 else -1.4
        poly([(x-2,y-1.3),(x+2,y-1.4),(x+2.5,y+.8),(x,y+1.5),(x-2.5,y+.7)],p.bone,p.ink,.65)
    # Near ribs curve toward the sternum. The abdomen is open.
    for j in range(6):
        y=34-j*4.15; radius=(8,11,13,13,12,9)[j]
        pts=bezier(q(-2,y),q(radius*.65,y+1),q(radius+2,y-4),q(8.5-j*.25,y-6.2),n=11)
        c.line(pts,p.ink,3.7*scale); c.line(pts,p.bone,2.15*scale)
        c.line(pts[1:7],p.light,.9*scale)
    line([(8.2,28),(8.5,20),(7,12)],p.ink,3.6)
    line([(8.2,28),(8.5,20),(7,12)],p.bone,2.1)
    # Collar bones and a visible shoulder blade.
    poly([(-5,38),(-10,33),(-6,25),(-2,31)],p.shade,p.ink,.8)
    line([(-11,37),(-4,40),(1,38),(10,36)],p.ink,4.)
    line([(-11,37),(-4,40),(1,38),(10,36)],p.bone,2.6)
    # Cervical vertebrae join the skull to the top of the chest.
    for y in (43,46,49):
        poly([(-3,y-1.7),(1.6,y-1.7),(2.0,y+.8),(-.2,y+1.6),(-3.3,y+.7)],p.bone,p.ink,.7)
    # Pelvic ring: two lobes and obturator openings.
    poly([(-10,5),(-12,0),(-8,-6),(-4,-7),(1,-3),(6,-7),(10,-5),
          (12,0),(9,5),(4,3),(1,0),(-3,3)],p.bone,p.ink,1.15)
    poly([(-8,1),(-4,1),(-3,-3),(-7,-4)],p.cavity)
    poly([(5,1),(8,1),(8,-3),(5,-4)],p.cavity)
    line([(-10,4),(-6,4),(-3,2)],p.light,1.1)
    line([(5,3),(9,4)],p.light,1.1)


def leg(c, points, palette=IVORY, far=False, scale=1., foot_angle=0.):
    hip,knee,ankle=points
    long_bone(c,hip,knee,3.2*scale,palette,far)
    paired_bones(c,knee,ankle,2.7*scale,palette,far)
    foot(c,ankle,foot_angle,scale,palette,far)


def arm(c, points, palette=IVORY, far=False, scale=1., hand_angle=0., grip=False):
    shoulder,elbow,wrist=points
    long_bone(c,shoulder,elbow,2.6*scale,palette,far)
    paired_bones(c,elbow,wrist,2.35*scale,palette,far)
    hand(c,wrist,hand_angle,scale,palette,far,grip)
