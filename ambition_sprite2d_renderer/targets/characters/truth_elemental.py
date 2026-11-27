"""Truth Elemental, a Math Dimension construct of living mathematical type.

The main silhouette is top (True), rendered as a living ink glyph. Its
parenthesis-shaped appendages close into () during the tell, a literal
unit inhabitant, then a Halmos square punctuates the release.
No glass, refraction, or literal simulation of a proof system is involved.
The existing ranged controller owns the projectile and damage window.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

from ._clockwork_enemy_art import Canvas, add, rot, track, phase, bezier, mix
from ._replicator_radical_art import floating_actor
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'truth_elemental'
FRAME_SIZE = (320, 256)
CENTER = (146., 124.)
WINDUP, FIRE, RECOVERY = .68, .18, .90
ROWS = [('idle', 24, 60), ('walk', 24, 50), ('run', 24, 40),
        ('notice', 10, 60), ('aim', 22, 31), ('windup', 22, 31),
        ('shoot', 6, 30), ('hit', 10, 55), ('death', 24, 55)]
LOOPS = {'idle', 'walk', 'run'}
TRAITS = ['elemental', 'truth', 'logic', 'proof']
ACTOR_METADATA = floating_actor(TARGET_NAME, 'Truth Elemental', 'math', TRAITS,
    'A living calligraphic True glyph. Its parenthetical limbs form the unit inhabitant (), and a black square marks the end of its attack.',
    'A floating ranged enemy. Its parentheses form the unit inhabitant before a Halmos square punctuates the attack; the projectile remains engine-owned.')
ACTOR_METADATA['body']['body_kind'] = 'Floating'
ACTOR_METADATA['body']['mass_class'] = 'Medium'
ACTOR_METADATA['actions'] = {'default_preset': 'truth_elemental_revelation'}
ACTOR_METADATA['animation_bindings'].update({
    'locomotion.run': {'animation': 'run', 'events': []},
    'action.ranged.primary': {'animation': 'shoot', 'events': [
        {'t': 0., 'event': 'projectile_release', 'source': 'truth_elemental.revelation'}]},
})

# Ink cut from a page, with a warm paper keyline.  The restrained teal
# accent is a secondary print color, not an elemental glow.
EDGE = '#15131e'
INK = '#454158'
INK_LIGHT = '#676079'
INK_DARK = '#15131e'
PAPER = '#eadcc0'
PAPER_SHADOW = '#a89c87'
WHITE = '#fff4d9'
TEAL = '#8ccbbf'
TEAL_DARK = '#477e79'


@dataclass(frozen=True)
class Pose:
    cycle: float = 0.
    align: float = 0.
    flash: float = 0.
    bob: float = 0.
    lean: float = 0.
    x: float = 0.
    alert: float = 0.
    hurt: float = 0.
    death: float = 0.


def pose(anim, i, n):
    t = phase(i, n, anim in LOOPS)
    p = math.tau * (t % 1.)
    if anim in LOOPS:
        speed = {'idle': 0., 'walk': .55, 'run': 1.}[anim]
        return Pose(p, bob=3.2*math.sin(p), lean=3.5*speed+1.2*math.sin(p), x=2*speed*math.cos(p))
    if anim == 'notice':
        u = track(t, [(0,0),(.55,1),(1,1)])
        return Pose(align=.16*u, alert=u, bob=-3*u, lean=-2*u)
    if anim in ('aim', 'windup'):
        u = track(t, [(0,0),(.2,.10),(.8,.94),(1,1)])
        return Pose(align=u, alert=u, bob=-4*u, x=-3*u, lean=-4*u)
    if anim == 'shoot':
        u = track(t, [(0,1),(.36,1),(1,0)])
        flash = track(t, [(0,1),(.22,.85),(.75,.12),(1,0)])
        return Pose(align=u, flash=flash, alert=u, bob=-4*u, x=-3*u, lean=-4*u+6*flash)
    if anim == 'hit':
        u = math.sin(math.pi*t)
        return Pose(hurt=u, x=-9*u, lean=-9*u, alert=u)
    if anim == 'death':
        return Pose(death=track(t, [(0,0),(.18,.08),(.80,1),(1,1)]))
    raise ValueError(anim)


def _path(start, curves, n=14):
    points = [start]
    for b,c,end in curves:
        points.extend(bezier(points[-1], b, c, end, n=n)[1:])
    return points


def _ink_shape(c, P, pts, *, far=False):
    """A thin paper cutout border around a dark printed stroke."""
    c.poly([P(x+2.2,y+3.0) for x,y in pts],PAPER_SHADOW,EDGE,6.0)
    c.poly([P(*v) for v in pts],INK_LIGHT if far else INK,EDGE,7.0)
    c.line([P(*v) for v in pts],PAPER_SHADOW if far else PAPER,4.6,closed=True)


def _paren(c, P, center, size, angle, side, *, far=False, charge=0.):
    """A tapered, weight-bearing typographic parenthesis."""
    def F(x,y):
        return P(*add(center,rot((side*x*size,y*size),angle)))
    pts = _path((11,-37), [((-10,-28),(-19,-14),(-19,0)),
        ((-19,15),(-10,29),(11,37)), ((-1,25),(-8,12),(-8,0)),
        ((-8,-13),(-1,-25),(11,-37))])
    # Smaller witness punctuation must not gain a disproportionately thick
    # outline when the symbols contract.
    line_scale=.55+.45*size
    c.poly([F(x+2,y+2) for x,y in pts],PAPER_SHADOW,EDGE,5.5*line_scale)
    c.poly([F(*p) for p in pts],INK_LIGHT if far else INK,EDGE,6.0*line_scale)
    c.line([F(*p) for p in pts],TEAL if charge>.65 else PAPER,3.0*line_scale,closed=True)
    c.line([F(*p) for p in _path((2,-29),[((-9,-19),(-15,-10),(-15,1)),((-15,10),(-10,20),(0,28))])],PAPER_SHADOW if far else INK_LIGHT,2.1*line_scale)


def _glyph(c,P,q):
    # The horizontal stroke is still continuous and the stem is unbroken:
    # the silhouette is top, not a head mounted on a humanoid body.
    a,h=q.align,q.hurt
    outline = _path((-53,-65), [((-36,-72),(23,-74),(51,-66)),
        ((56,-64),(57,-57),(55,-50)), ((54,-43),(51,-35),(47,-34)),
        ((35,-36),(23,-36),(15,-34)), ((14,-11),(14,28),(17,55)),
        ((18,61),(20,64),(20,67)), ((10,71),(-10,71),(-20,66)),
        ((-16,40),(-15,2),(-17,-34)), ((-28,-36),(-43,-34),(-50,-34)),
        ((-54,-39),(-58,-53),(-57,-59)), ((-56,-62),(-55,-64),(-53,-65))])
    _ink_shape(c,P,outline)
    # Subtle ink facets, on the same connected silhouette. Avoid the thick
    # extruded block of the earlier version.
    c.poly([P(*v) for v in [(-51,-62),(-28,-67),(10,-68),(48,-63),(51,-58),(20,-63),(-25,-61),(-51,-56)]],INK_LIGHT,None)
    c.line([P(-48,-64),P(-29,-68),P(13,-69),P(45,-65)],WHITE,1.35)
    c.poly([P(*v) for v in [(-11,-30),(-5,-32),(-4,17),(-6,53),(-10,61),(-10,21)]],INK_LIGHT,None)
    c.line([P(-13,-24),P(-12,14),P(-13,45)],PAPER_SHADOW,1.4)
    c.poly([P(*v) for v in [(9,-30),(14,-31),(15,22),(18,61),(8,64),(9,17)]],INK_DARK,None)
    c.line([P(12,27),P(14,52)],TEAL_DARK,1.45)
    c.line([P(-10,65),P(1,67),P(10,65)],TEAL_DARK,1.9)
    # Confident, slightly asymmetrical ink-cut eyes. At game scale the
    # paper-white silhouettes and large dark pupils carry the expression.
    blink=1-.94*max(0.,1-abs(q.cycle/math.tau-.77)/.055) if q.cycle else 1.
    open_y=max(.7,(10.1-3.1*a)*(1-.76*h)*blink)
    for ex,w,shift in [(-17,11.2,2.6),(16,12.6,3.5)]:
        ey=-50.
        lid=_path((ex-w,ey-2*a), [((ex-w*.48,ey-open_y-2*a),(ex+w*.53,ey-open_y+2*a),(ex+w,ey-1+2*a)),
            ((ex+w*.55,ey+open_y),(ex-w*.52,ey+open_y),(ex-w,ey-2*a))])
        c.poly([P(*v) for v in lid],WHITE,None)
        if open_y>2:
            ix=ex+shift+1.2*a
            c.oval(P(ix,ey),4.2,max(1.,open_y*.88),INK_DARK,None,angle=q.lean)
            c.disk(P(ix-1.0,ey-2.2),1.15,WHITE,None)
        brow=_path((ex-w-1,ey-11+4*a),[((ex-5,ey-15+3*a),(ex+4,ey-15+5*a),(ex+w+1,ey-10+5*a))])
        c.line([P(*v) for v in brow],PAPER_SHADOW if a<.3 else TEAL,2.25)
    # A knowing half-smile, laid across the transition into the stem.
    mouth=_path((-7,-38),[((-1,-33+a),(6,-32-2*a),(11,-39-2*a))])
    c.line([P(*v) for v in mouth],WHITE,2.6)


def _square(c,P,x,y,side, *, accent=0.):
    # A filled Halmos mark. Its paper keyline makes black visible in the
    # darker rooms without turning it into a hollow square.
    r=side/2
    corners=[(x-r,y-r),(x+r,y-r),(x+r,y+r),(x-r,y+r)]
    c.poly([P(*v) for v in corners],INK_DARK,PAPER,2.0)
    if accent>0:
        c.line([P(x-r-3,y-r),P(x-r-3,y+r)],TEAL,1.6*accent+.6)


def _render_frame(anim,i,n):
    q=pose(anim,i,n)
    a,p,d=q.align,q.cycle,q.death
    c=Canvas(FRAME_SIZE)
    # The proof mark persists briefly after the glyph contracts away.
    # Its appearance is timed to the contraction, not a separate projectile.
    if d>=.54:
        s=track(d,[(.54,1),(.76,1),(1,0)])
        if s<=0: return c.finish()
        r=track(d,[(.54,22),(.72,23),(1,12)])
        def S(x,y): return add(CENTER,(x,y))
        _square(c,S,0,0,r)
        im=c.finish();im.putalpha(im.getchannel('A').point(lambda v:round(v*s)))
        return im
    shrink=1-track(d,[(0,0),(.20,0),(.54,.85)])
    origin=add(CENTER,(q.x,q.bob))
    # A little flex in the stem makes the printed glyph feel alive. It is
    # a bounded shear of the lower stroke, not an articulated human rig.
    def P(x,y):
        k=max(0.,(y+32)/100.)
        bend=k*k*(5.2*math.sin(p)-6*a+5*q.hurt)
        # Contract slightly during the tell, then recoil on discharge.
        sx=1+.045*a-.035*q.flash
        sy=1-.045*a+.045*q.flash
        return add(origin,rot(((x+bend)*shrink*sx,y*shrink*sy),q.lean))
    sway=math.sin(p)
    # Parentheses actually form () rather than containing a generic orb.
    # The empty interior is deliberate: () is the unit inhabitant itself.
    left=mix((-44.,20.+4*sway),(43.-5*q.flash,-1.),a)
    right=mix((46.,22.-4*sway),(75.+5*q.flash,-1.),a)
    # Sweep under the stem on the way to the witness, as if a line of
    # notation is being assembled. Keep the far stroke behind the body.
    left=add(left,(0.,39*math.sin(math.pi*a)))
    size=1-.52*a
    _paren(c,P,left,size,-9*(1-a)+4*sway*(1-a),1,far=True,charge=a)
    _glyph(c,P,q)
    _paren(c,P,right,size,9*(1-a)-4*sway*(1-a),-1,charge=a)
    if a>.05:
        # Two short proof-rule strokes guide the eye to the witness. They
        # appear only during the final part of the aim, at the muzzle.
        strength=track(a,[(0,0),(.48,0),(1,1)])
        x,y=59.,-1.
        if strength>.02 and q.flash<=.02:
            w=11*strength
            c.line([P(x-w,y+19),P(x+w,y+19)],PAPER_SHADOW,1.5)
            c.line([P(x-w*.7,y-19),P(x+w*.7,y-19)],TEAL,1.4)
        if q.flash>.02:
            _square(c,P,x,y,18+7*q.flash,accent=q.flash)
            for dx,dy in [(-1,-1),(1,-1),(1,1),(-1,1)]:
                inner=12+3*q.flash;outer=inner+8*q.flash
                c.line([P(x+dx*inner,y+dy*inner),P(x+dx*outer,y+dy*outer)],PAPER,1.5)
    im=c.finish()
    return im


def _metrics(fw,fh):
    # Preserve the original gameplay body box, excluding detached glyphs.
    return body_metrics_for_box((100,48,195,202),fw,fh)


def render(out_dir: str | Path, **opts):
    from ...authoring.sheet_build import build_sheet
    outputs=build_sheet(target=TARGET_NAME,rows=ROWS,render_fn=_render_frame,
        out_dir=Path(out_dir),frame_size=FRAME_SIZE,auto_crop=False,
        actor_metadata=ACTOR_METADATA,body_metrics_fn=_metrics,
        animation_key_map={a:a for a,_,_ in ROWS},pose_bodies='authored')
    return [outputs[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]
