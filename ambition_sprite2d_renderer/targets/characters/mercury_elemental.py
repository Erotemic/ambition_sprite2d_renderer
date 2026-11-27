"""Mercury elemental: a moving mass of reflective liquid metal.

The movement is an authored animation, not a fluid simulation. The puddle is
part of the creature. The dark and light bands suggest reflections from its
curved surface; they are not separate layers of material.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from ._clockwork_enemy_art import Canvas, bezier, phase, track, polar, add, rot
from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'mercury_elemental'
DISPLAY_NAME = 'Mercury Elemental'
FRAME_SIZE = (340, 250)
CX, GROUND = 137., 223.
WINDUP_S, ACTIVE_S, RECOVER_S = .54, .16, .68
TOTAL_S = WINDUP_S + ACTIVE_S + RECOVER_S
ACTIVE_START = WINDUP_S / TOTAL_S
ACTIVE_END = (WINDUP_S + ACTIVE_S) / TOTAL_S
ROWS = [('idle', 24, 60), ('walk', 24, 48), ('run', 24, 35),
        ('notice', 9, 60), ('windup', 18, 30), ('attack_side', 42, 33),
        ('hit', 9, 60), ('death', 24, 50), ('death_idle', 1, 200)]
LOOPS = {'idle', 'walk', 'run', 'death_idle'}
TRAITS = ['enemy', 'science', 'elemental', 'chemical_element', 'mercury', 'liquid_metal', 'no_hands']
ACTOR_METADATA = {
    'actor': {'character_id': TARGET_NAME, 'display_name': DISPLAY_NAME},
    'body': {'body_plan': 'Crawler', 'body_kind': 'Standard', 'mass_class': 'Heavy',
             'locomotion_hint': 'Slither', 'traits': TRAITS},
    'capabilities': {'traversal': {'walk': True}},
    'actions': {'default_preset': 'mercury_elemental_thrust'},
    'visual': {'default_pose': 'idle', 'portrait': {'animation': 'idle', 'frame': 0}},
    'animation_bindings': {
        'default': {'animation': 'idle', 'events': []},
        'locomotion.walk': {'animation': 'walk', 'events': []},
        'locomotion.run': {'animation': 'run', 'events': []},
        'combat.hurt': {'animation': 'hit', 'events': []},
        'combat.death': {'animation': 'death', 'events': []},
        'action.melee.primary': {'animation': 'attack_side', 'events': [
            {'t': ACTIVE_START, 'event': 'hitbox_active_start', 'source': 'mercury_elemental.thrust'},
            {'t': ACTIVE_END, 'event': 'hitbox_active_end', 'source': 'mercury_elemental.thrust'},
        ]},
    },
    'tags': TRAITS,
    'authoring_description': 'A Science Dimension creature made from mercury (Hg), the silver-colored liquid metal. Its flowing body has high-contrast mirror reflections and small round drops. Its shape-changing attacks are fictional.',
    'gameplay_description': 'A heavy ground-based enemy that flows along the floor. It draws its mass back before extending a narrow metallic spike. On defeat it collapses into a pool of silver beads.',
}

EDGE = '#28303a'
DARK = '#343d47'
WHITE = '#f5fafb'


@dataclass(frozen=True)
class Pose:
    cycle: float = 0.
    moving: float = 0.
    ready: float = 0.
    strike: float = 0.
    recover: float = 0.
    hurt: float = 0.
    death: float = 0.
    notice: float = 0.


def pose(anim, i, n):
    t = phase(i, n, anim in LOOPS)
    p = math.tau * (t % 1.)
    if anim == 'idle':
        return Pose(cycle=p)
    if anim in ('walk', 'run'):
        return Pose(cycle=p, moving=.7 if anim == 'walk' else 1.)
    if anim == 'notice':
        return Pose(cycle=p, notice=track(t, [(0, 0), (.45, 1), (1, .35)]))
    if anim == 'windup':
        return Pose(cycle=p, ready=track(t, [(0, 0), (.85, 1), (1, 1)]))
    if anim == 'attack_side':
        a, b = ACTIVE_START, ACTIVE_END
        k = lambda keys: track(t, keys)
        # The separate windup and the active boundary share the same pose.
        flow = t/a if t <= a else 1 + (t-a)/(1-a)
        return Pose(cycle=math.tau*(flow % 1.),
                    ready=k([(0, 0), (.85*a, 1), (a, 1), (a+.045, 0), (1, 0)]),
                    strike=k([(0, 0), (a, 0), (a+.04, 1), (b, 1), (b+.12, .18), (1, 0)]),
                    recover=k([(0, 0), (b, 0), (b+.16, 1), (1, 0)]))
    if anim == 'hit':
        return Pose(cycle=p, hurt=math.sin(math.pi*t))
    if anim in ('death', 'death_idle'):
        d = 1. if anim == 'death_idle' else track(t, [(0, 0), (.12, .02), (.76, 1), (1, 1)])
        return Pose(cycle=0., death=d)
    raise ValueError(anim)


def contour(start, *segments):
    pts = [start]
    for a, b, end in segments:
        pts.extend(bezier(pts[-1], a, b, end, n=14)[1:])
    return pts


def stroke(c, P, start, *segments, color=WHITE, width=2.):
    c.line([P(*p) for p in contour(start, *segments)], color, width)


# A reflected light/dark horizon with a narrow highlight and a second rim.
# Keep the colors neutral, with a slightly cool dark reflection and a warm rim.
_STOPS = np.array([-.10, .03, .12, .25, .36, .395, .43, .48, .57, .62, .68, .75, .80, .88, .96, 1.15])
_COLORS = np.array([(166,177,185), (222,229,232), (249,251,249), (181,197,205),
                    (149,165,175), (179,190,193), (59,72,85), (34,43,54), (61,72,84),
                    (119,134,145), (200,211,212), (236,240,231), (142,155,164), (83,94,104), (53,63,73), (135,145,154)])


def _chrome(c, points, cycle, *, shade=1., shift=0., outline=True, glint=True):
    """Paint reflection bands inside the outline of one liquid-metal lobe."""
    # Limit work to the local bounding rectangle. Use the existing Canvas at
    # its supersampled resolution, so the material and line art share edges.
    s = c.s
    x0 = max(0, math.floor(min(p[0] for p in points)*s))
    y0 = max(0, math.floor(min(p[1] for p in points)*s))
    x1 = min(c.image.width, math.ceil(max(p[0] for p in points)*s)+1)
    y1 = min(c.image.height, math.ceil(max(p[1] for p in points)*s)+1)
    if x1 <= x0 or y1 <= y0:
        return
    w, h = x1-x0, y1-y0
    mask = Image.new('L', (w, h))
    ImageDraw.Draw(mask).polygon([(x*s-x0, y*s-y0) for x,y in points], fill=255)
    yy, xx = np.ogrid[0:h, 0:w]
    u = 2*xx/max(1,w-1)-1
    v = yy/max(1,h-1)
    # Reflection contours bend across the rounded surface and slip a little
    # during deformation. They do not scroll in screen space.
    b = v + .095*u*u + .045*u + .026*np.sin(cycle+u*2+v*4) + .043*np.sin(4*u+v*7) + shift
    rgb = np.stack([np.interp(b, _STOPS, _COLORS[:, j]) for j in range(3)], axis=-1)
    edge = np.clip(1.-.18*np.abs(u)**3, .72, 1.)
    rgb *= (shade*edge)[..., None]
    # A soft, small high light above the principal reflection boundary.
    if glint:
        spot = np.exp(-((u+.39)/.27)**2-((v-.16)/.095)**2)*.42
        rgb += (255-rgb)*spot[..., None]
    im = Image.fromarray(np.clip(rgb, 0, 255).astype('uint8')).convert('RGBA')
    c.image.paste(im, (x0,y0), mask)
    if outline:
        c.line(points, EDGE, 1.65, closed=True)


def _lobe(c, P, cycle, start, *segments, shade=1., shift=0., outline=True):
    _chrome(c, [P(*p) for p in contour(start, *segments)], cycle,
            shade=shade, shift=shift, outline=outline)


def _bead(c, center, rx, ry, cycle, angle=0., shade=1.):
    # Rounded drops have the same material as the body, not water-blue fill.
    pts = [add(center, rot((rx*v[0], ry*v[1]), angle))
           for v in (polar(1., 360*i/40) for i in range(40))]
    _chrome(c, pts, cycle, shade=shade, shift=-.025)
    if rx > 3.5 and ry > 3.5:
        c.oval((center[0]-.32*rx,center[1]-.34*ry),rx*.20,ry*.10,WHITE,None,angle=-28)


def _paint(c, q):
    p, r, h, d = q.cycle, q.ready, q.strike, q.death
    flow, hurt = q.moving, q.hurt
    wave = math.sin(p)
    # Maintain the floor while the body lengthens and squashes. Upper material
    # moves more than the low, heavy pool. There are no rigid limb chains.
    width = 1+.18*flow+.14*r+.13*h+.10*q.recover+.08*hurt+.32*d
    # Broad and narrow phases alternate; the foot line does not move up.
    breathe=(.027+.045*flow)*math.cos(p)*(1-d)
    width *= 1+breathe
    height = (1-.12*flow+.09*r-.18*h-.14*q.recover-.12*hurt+.045*q.notice)*(1-.87*d)/(1+breathe)
    def P(x,y):
        u = max(0.,min(1.,-y/155.))
        bend = (14*flow - 12*r + 17*h - 9*hurt)*u
        wavex = (4.8+9*flow)*math.sin(p+y*.045)*u*(1-d)
        # The low pool flows from the back edge toward the front. The top
        # and bottom move out of phase, as in a slow peristaltic wave.
        pool=(1-u)**3*(2.5+7*flow)*math.sin(p-x*.028)*(1-d)
        return CX+x*width+bend+wavex+pool, GROUND+y*height+3*wave*u*(1-d)

    # Behind the main body: a curved, thick tendril that lifts and subsides.
    # At death it merges into the same puddle instead of leaving a rigid arm.
    if d < 1.:
        bx = -66 - 9*r - 5*flow + 7*math.sin(p+1.1)
        by = -92 - 20*r + 12*h + 13*math.cos(p+.8)
        _lobe(c,P,p,(-26,-96),
              ((-42,-116),(bx-16,by-20),(bx-17,by-2)),
              ((bx-19,by+17),(bx-6,by+23),(bx+11,by+14)),
              ((bx+21,by+8),(bx+17,by-1),(bx+6,by-2)),
              ((bx-1,by+7),(bx-8,by+2),(bx-5,by-5)),
              ((bx+1,by-19),(-40,-83),(-24,-76)),
              ((-15,-78),(-19,-91),(-26,-96)),shade=.86,shift=.018)
    # The entire central silhouette is a single mass: bulbous pool, narrowed
    # waist, rising shoulder, head, and attached forward spike.
    ex=65+71*h-12*r+5*math.sin(p+.6)*(1-h)
    ey=-66-20*r+7*h+6*math.cos(p-.5)*(1-h)
    # The tip changes from a rounded lobe to a narrow, forward strike.
    tip_height=18*(1-h)+2.2*h
    _lobe(c,P,p,(-65,0),
          ((-88,-1),(-86,-17),(-65,-22)),
          ((-40,-24),(-40,-42),(-48,-63)),
          ((-60,-88),(-47,-111),(-24,-112)),
          ((-26,-132),(-10,-152),(11,-154)),
          ((31,-157),(45,-144),(47,-126)),
          ((57,-119),(59,-110),(50,-104)),
          ((45,-101),(53,-96),(45,-86)),
          ((47,-81),(56,-83),(ex-20,ey-14)),
          ((ex-8,ey-13),(ex+5,ey-tip_height),(ex+7,ey)),
          ((ex+4,ey+tip_height),(ex-9,ey+16),(ex-22,ey+17)),
          ((50,-49),(30,-57),(26,-44)),
          ((19,-27),(48,-25),(69,-19)),
          ((90,-11),(88,-1),(67,0)),
          ((21,0),(-27,0),(-65,0)))

    # More local reflection bands describe the cheek, shoulder, and waist.
    # These have no hard outlines: they are changes in surface curvature.
    if d < .95:
        c.poly([P(*a) for a in contour((-25,-110),((-39,-99),(-39,-87),(-30,-76)),
                  ((-36,-99),(-17,-104),(3,-103)),((3,-112),(-11,-117),(-25,-110)))], '#b9c6cc',None)
        stroke(c,P,(-8,-145),((6,-153),(24,-149),(35,-138)),color=WHITE,width=2.2*(1-d)+.4)
        stroke(c,P,(-42,-98),((-47,-89),(-41,-78),(-37,-72)),color='#e7edef',width=2.2*(1-d)+.4)
        stroke(c,P,(-33,-59),((-27,-47),(-25,-31),(-35,-23)),color='#d7e0e2',width=2.5*(1-d)+.4)
        # The crest of a raised shoulder catches a thin, bright reflection.
        stroke(c,P,(-30,-105),((-22,-112),(-10,-110),(-5,-106)),color=WHITE,width=2.0*(1-d)+.3)
        # A curved secondary highlight moves down the bulge in its side.
        v=4*math.sin(p+.6)
        stroke(c,P,(-18,-44+v),((-7,-39+v),(5,-38+v),(13,-42+v)),color='#e6ece9',width=1.7*(1-d)+.3)
        # An elongated highlight moves along the attached attacking lobe.
        if ex > 62:
            stroke(c,P,(45,-77),((56,-80),(ex-22,ey-8),(ex-4,ey-3)),color=WHITE,width=2.1*(1-d)+.4)
            stroke(c,P,(38,-58),((55,-55),(ex-25,ey+12),(ex-10,ey+8)),color='#86929d',width=1.9*(1-d)+.3)
        else:
            stroke(c,P,(ex-9,ey-7),((ex-4,ey-11),(ex+1,ey-9),(ex+3,ey-4)),color=WHITE,width=1.6*(1-d)+.4)
        # Small deep eye sockets, not painted-on white eyeballs. The smooth
        # cheek remains metallic. Render face after the appendages.
        face_weight=max(0.,1-d*1.6)
        if face_weight > .04:
            blink = .90*hurt
            e = 3.2*(1-blink)*face_weight
            # The inner brow slopes down toward the nose. A dark slit
            # remains visible in every expression; the lit edge is a reflection.
            for x,y,w,tilt in [(5,-129,10,1),(31,-127,8,-1)]:
                slope=3.8+2.2*r+1.4*h
                c.poly([P(x-w-2,y-4-slope*tilt),P(x+w+1,y-4+slope*tilt),
                        P(x+w-1,y+e+1+slope*tilt),P(x-w+1,y+e+1-slope*tilt)],'#283039',None)
                stroke(c,P,(x-w+2,y+e-slope*tilt),
                       ((x-3,y+e-slope*tilt*.3),(x+3,y+e+slope*tilt*.3),(x+w-1,y+e+slope*tilt)),
                       color='#aab5bc',width=1.05)
            # A tiny black fold at the jaw and a second reflected rim.
            stroke(c,P,(15,-111),((24,-114),(38,-111),(44,-113-2*r)),color=EDGE,width=2.4*(1-d)+.3)
            stroke(c,P,(18,-107),((26,-109),(37,-107),(43,-109)),color='#f0f3f1',width=1.1)
            stroke(c,P,(36,-136),((40,-133),(42,-129),(44,-125)),color='#c9d1d4',width=1.7)
    # The low pool has its own curved reflected rim. It is the physical body
    # silhouette, not a contact shadow.
    stroke(c,P,(-66,-11),((-48,-16),(-24,-7),(-9,-9)),color='#eef3ee',width=2.1)
    stroke(c,P,(3,-11),((18,-19),(40,-19),(66,-9)),color='#cdd7d9',width=1.9)

    # Periodic droplets detach and reconnect with the pool. Each arch starts
    # and ends inside the main contour. Size is zero at the cycle seam.
    if d < 1:
        for j in range(4):
            f=(p/math.tau+j/4)%1.
            life=math.sin(math.pi*f)**.8
            if life < .10: continue
            side=-1 if j%2==0 else 1
            span=(21+17*flow+12*hurt+18*h)*math.sin(math.pi*f)
            x=side*(54+span)
            y=-10-(21+20*flow+18*h)*4*f*(1-f)
            rad=(3.5+1.4*(j%2))*life*(1-.4*d)
            _bead(c,P(x,y),rad*(1+.35*abs(.5-f)),rad, p+j,angle=side*(35-70*f))
    # Death leaves real silver beads beside the pool. The terminal frame is
    # identical to the resting frame. The face and tendrils have dissolved.
    if d > .01:
        # Three rounded globules rise out of the collapsing pool as surface
        # tension rounds its mass. They stay connected at the base.
        for x, rx, ry in [(-39,26,12),(3,31,15),(45,23,10)]:
            k=max(0., (d-.55)/.45)
            if k > .01:
                _bead(c,(CX+x,GROUND-ry*k),rx*k,ry*k,p,shade=.98)
        for side, x, radius, arc_height in [(-1,94,8,25),(1,97,7,19),(1,116,4,37)]:
            v=d
            k=radius*min(1,2*v)
            px=CX+side*(46+(x-46)*v)
            py=GROUND-k-arc_height*4*v*(1-v)
            _bead(c,(px,py),k*1.15,k,p,shade=.97)


def _render_frame(anim, i, n):
    c=Canvas(FRAME_SIZE)
    _paint(c,pose(anim,i,n))
    return c.finish()


def _body_metrics(w,h):
    # Exclude detached drops and the extended weapon from the standing box.
    return body_metrics_for_box((83, 67, 195, 225), w,h)


def render(out_dir: str | Path, **opts):
    result=build_sheet(target=TARGET_NAME,rows=ROWS,render_fn=_render_frame,
                       out_dir=Path(out_dir),frame_size=FRAME_SIZE,auto_crop=False,
                       actor_metadata=ACTOR_METADATA,body_metrics_fn=_body_metrics,
                       animation_key_map={a:a for a,_,_ in ROWS},sits_on_ground=True)
    return [result[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]
