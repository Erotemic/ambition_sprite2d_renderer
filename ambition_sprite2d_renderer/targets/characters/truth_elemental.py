"""Truth Elemental, a Math Dimension construct of living mathematical type.

The main silhouette is top (True). Parenthesis-shaped appendages frame a
single witness during the tell, then a Halmos square punctuates the release.
The witness dot is illustrative, not the syntax of the unit inhabitant ().
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
    'An animated top symbol in the shape of a typeset mathematical glyph. A pair of parentheses frames a unique witness, and a black square marks the end of its attack.',
    'A floating ranged enemy. It gathers a witness before punctuating the attack with a Halmos square; the projectile remains engine-owned.')
ACTOR_METADATA['body']['body_kind'] = 'Floating'
ACTOR_METADATA['body']['mass_class'] = 'Medium'
ACTOR_METADATA['actions'] = {'default_preset': 'truth_elemental_revelation'}
ACTOR_METADATA['animation_bindings'].update({
    'locomotion.run': {'animation': 'run', 'events': []},
    'action.ranged.primary': {'animation': 'shoot', 'events': [
        {'t': 0., 'event': 'projectile_release', 'source': 'truth_elemental.revelation'}]},
})

# Warm paper and dark ink, with a restrained brass witness accent.
# The outline is important on dark Math Dimension backgrounds.
EDGE = '#17151c'
INK = '#27232e'
INK_LIGHT = '#403b48'
INK_DARK = '#17141e'
PAPER = '#f4e9d4'
PAPER_SHADOW = '#c7bda9'
GRAPHITE = '#736d77'
WHITE = '#fff8e6'
GOLD = '#e8b966'
GOLD_SHADOW = '#a36f39'
PAPER_DEEP = '#978e83'
PAPER_MID = '#dcd0b7'
PAPER_LIGHT = '#fdf2dc'


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
        return Pose(align=u, alert=u, bob=-2*u, x=-3*u, lean=-4*u)
    if anim == 'shoot':
        u = track(t, [(0,1),(.36,1),(1,0)])
        flash = track(t, [(0,1),(.22,.85),(.75,.12),(1,0)])
        return Pose(align=u, flash=flash, alert=u, bob=-2*u, x=-3*u, lean=-4*u+6*flash)
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


def _paren(c, P, center, size, angle, side, *, far=False):
    """An actual tapered parenthesis, not a tube or a separate arm rig."""
    def F(x,y):
        return P(*add(center,rot((side*x*size,y*size),angle)))
    # Outer and inner contours meet at the two pointed ink terminals.
    pts = _path((12,-37), [((-8,-26),(-15,-12),(-15,0)),
        ((-15,14),(-7,29),(12,37)), ((1,25),(-4,12),(-4,0)),
        ((-4,-13),(1,-26),(12,-37))])
    c.poly([F(*p) for p in pts],PAPER_DEEP if far else PAPER_MID,EDGE,2.4)
    c.line([F(*p) for p in _path((9,-32),[((-5,-24),(-11,-11),(-11,0)),((-11,12),(-5,23),(7,31))])],PAPER_SHADOW if far else PAPER_LIGHT,3.0)
    c.line([F(*p) for p in _path((3,-27),[((-5,-19),(-8,-9),(-8,-2))])],PAPER_LIGHT,1.1)


def _glyph(c,P,q):
    # A genuine top symbol silhouette, with a broad head/crossbar and one
    # unbroken vertical stem. Small calligraphic terminals rather than facets.
    a,h=q.align,q.hurt
    outline = _path((-50,-70), [((-21,-72),(24,-72),(49,-70)),
        ((54,-70),(56,-66),(56,-62)), ((56,-53),(55,-40),(54,-33)),
        ((44,-30),(22,-31),(15,-31)), ((14,-2),(15,35),(18,65)),
        ((8,71),(-7,71),(-17,65)), ((-14,37),(-14,4),(-15,-31)),
        ((-26,-31),(-44,-30),(-54,-33)), ((-57,-43),(-56,-61),(-54,-67)),
        ((-53,-69),(-52,-70),(-50,-70))])
    # Shallow letterpress thickness, not a crystal or mechanical shell.
    c.poly([P(x+5,y+6) for x,y in outline],PAPER_DEEP,EDGE,2.8)
    c.poly([P(*v) for v in outline],PAPER,EDGE,2.8)
    c.poly([P(*v) for v in [(-48,-66),(48,-66),(51,-63),(49,-59),(-48,-59)]],PAPER_LIGHT,None)
    c.line([P(-46,-66),P(46,-66)],WHITE,1.6)
    c.poly([P(*v) for v in [(-50,-37),(-17,-35),(-16,-32),(-51,-34)]],PAPER_MID,None)
    c.poly([P(*v) for v in [(17,-35),(51,-37),(51,-34),(16,-32)]],PAPER_MID,None)
    c.poly([P(*v) for v in [(-13,-29),(-5,-27),(-5,59),(-11,63)]],PAPER_LIGHT,None)
    c.poly([P(*v) for v in [(7,-30),(13,-30),(15,63),(7,66)]],PAPER_SHADOW,None)
    # A narrow paper-colored brush mark follows the stem, and ends before
    # the terminal. No unrelated glyphs or decorations on the body.
    c.line([P(-10,-25),P(-9,15),P(-9,47)],WHITE,1.2)
    c.line([P(-12,64),P(-3,66),P(8,66)],PAPER_DEEP,1.2)
    # Two expressive eyes carved directly from the horizontal ink stroke.
    # Keep them high enough that the bar remains a readable top symbol.
    blink=1-.93*max(0.,1-abs(q.cycle/math.tau-.77)/.055) if q.cycle else 1.
    open_y=max(.9,(9.2-2.4*a)*(1-.70*h)*blink)
    for ex,w,shift in [(-16,10.0,1.5),(15,12.0,2.1)]:
        ey=-50.
        lid=_path((ex-w,ey), [((ex-w*.48,ey-open_y),(ex+w*.53,ey-open_y),(ex+w,ey-1)),
            ((ex+w*.55,ey+open_y),(ex-w*.52,ey+open_y),(ex-w,ey))])
        c.poly([P(*v) for v in lid],WHITE,EDGE,1.4)
        if open_y>2:
            ix=ex+shift+1.8*a
            c.oval(P(ix,ey-.3),4.5,max(1.,open_y*.85),INK_DARK,None,angle=q.lean)
            c.disk(P(ix-1.1,ey-2.0),1.3,WHITE,None)
        brow=_path((ex-w-1,ey-10+3*a),[((ex-5,ey-13+3*a),(ex+4,ey-13+4*a),(ex+w+1,ey-9+4*a))])
        c.line([P(*v) for v in brow],INK,2.7)
    # A restrained, confident smile rather than a visor or robot face.
    mouth=_path((-7,-38),[((-1,-33-2*a),(7,-33-2*a),(10,-38))])
    c.line([P(*v) for v in mouth],INK,2.5)


def _square(c,P,x,y,side, *, accent=0.):
    # The Halmos mark is filled black, never a hollow crystal frame.
    # A thin light edge is a game-scale readability aid, not another symbol.
    r=side/2
    corners=[(x-r,y-r),(x+r,y-r),(x+r,y+r),(x-r,y+r)]
    c.poly([P(*v) for v in corners],INK_DARK,PAPER,1.65)
    if accent>0:
        c.line([P(x-r-2,y-r),P(x-r-2,y+r)],GOLD,1.5*accent+.6)


def _render_frame(anim,i,n):
    q=pose(anim,i,n)
    a,p,d=q.align,q.cycle,q.death
    c=Canvas(FRAME_SIZE)
    # The death animation ends the proof. Collapse to an actual black square
    # before vanishing, without visually suggesting that True became False.
    if d>=.54:
        s=track(d,[(.54,1),(.71,1),(1,0)])
        if s<=0: return c.finish()
        r=track(d,[(.54,22),(.72,23),(1,12)])
        def S(x,y): return add(CENTER,(x,y))
        _square(c,S,0,0,r)
        im=c.finish();im.putalpha(im.getchannel('A').point(lambda v:round(v*s)))
        return im
    shrink=1-track(d,[(0,0),(.20,0),(.54,.85)])
    origin=add(CENTER,(q.x,q.bob))
    def P(x,y): return add(origin,rot((x*shrink,y*shrink),q.lean))
    # Parentheses begin on either side of the glyph, then move as a pair to
    # frame precisely one witness in front of it. Their movement is not a
    # refraction effect; the contours are animated symbols in their own right.
    sway=math.sin(p)
    left=mix((-43.,21.+3*sway),(39.,0.),a)
    right=mix((44.,22.-3*sway),(79.,0.),a)
    # The far parenthesis remains behind the glyph as it moves forward.
    _paren(c,P,left,1-.51*a,-7*(1-a),1,far=True)
    _glyph(c,P,q)
    _paren(c,P,right,1-.51*a,7*(1-a),-1)
    if a>.05:
        # One witness, not a shower of generic magic particles. The point is
        # a diagrammatic representation of the unique inhabitant of Unit.
        # It stays at the existing projectile release offset.
        strength=track(a,[(0,0),(.45,.4),(1,1)])
        radius=2.2+5.4*strength
        x,y=59.,-1.
        if q.flash>.02:
            # The completed proof punctuates the discharge with a square.
            # No travelling baked projectile: runtime owns that object.
            _square(c,P,x,y,17+6*q.flash,accent=q.flash)
            for dx,dy in [(-1,-1),(1,-1),(1,1),(-1,1)]:
                inner=12+3*q.flash;outer=inner+8*q.flash
                c.line([P(x+dx*inner,y+dy*inner),P(x+dx*outer,y+dy*outer)],PAPER,1.5)
        else:
            c.disk(P(x,y),radius,GOLD_SHADOW,PAPER_SHADOW,1.2)
            c.disk(P(x-.6,y-.8),radius*.68,GOLD,None)
            c.disk(P(x-1.5,y-1.7),1.25,WHITE,None)
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
