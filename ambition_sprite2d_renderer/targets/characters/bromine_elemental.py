"""Bromine Elemental: a living mass of dark liquid and reddish vapor.

Bromine is a dark red-brown liquid at room temperature. The vapor and the
liquid have different colors and opacity. The attack and the face are fiction.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

from PIL import ImageChops

from ._clockwork_enemy_art import Canvas, phase, track, mix
from ._elemental_enemy_family import path, shape, stroke
from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'bromine_elemental'
DISPLAY_NAME = 'Bromine Elemental'
FRAME_SIZE = (360, 264)
CX, GROUND = 140., 237.
BODY_BOX = (91, 78, 207, 239)
PIVOT_X = (BODY_BOX[0] + BODY_BOX[2] - 1) / 2
TURN_ANGLE = math.radians(52)
WINDUP_S, ACTIVE_S, RECOVER_S = .60, .18, .72
TOTAL_S = WINDUP_S + ACTIVE_S + RECOVER_S
A, B = WINDUP_S / TOTAL_S, (WINDUP_S + ACTIVE_S) / TOTAL_S
ROWS = [('idle', 24, 60), ('walk', 24, 50), ('run', 24, 36),
        ('turnaround', 11, 20), ('notice', 9, 60), ('windup', 18, 33), ('attack_side', 46, 33),
        ('hit', 9, 60), ('death', 24, 55), ('death_idle', 1, 200)]
LOOPS = {'idle', 'walk', 'run', 'death_idle'}
TRAITS = ['enemy', 'science', 'elemental', 'chemical_element', 'bromine',
          'halogen', 'liquid', 'no_hands']
ACTOR_METADATA = {
    'actor': {'character_id': TARGET_NAME, 'display_name': DISPLAY_NAME},
    'body': {'body_plan': 'Crawler', 'body_kind': 'Standard',
             'mass_class': 'Medium', 'locomotion_hint': 'Slither', 'traits': TRAITS},
    'capabilities': {'traversal': {'walk': True}},
    'actions': {'default_preset': 'bromine_elemental_lash'},
    'visual': {'default_pose': 'idle', 'portrait': {'animation': 'idle', 'frame': 0}},
    'animation_bindings': {
        'default': {'animation': 'idle', 'events': []},
        'locomotion.walk': {'animation': 'walk', 'events': []},
        'locomotion.run': {'animation': 'run', 'events': []},
        'combat.hurt': {'animation': 'hit', 'events': []},
        'combat.death': {'animation': 'death', 'events': []},
        'action.melee.primary': {'animation': 'attack_side', 'events': [
            {'t': A, 'event': 'hitbox_active_start', 'source': 'bromine_elemental.lash'},
            {'t': B, 'event': 'hitbox_active_end', 'source': 'bromine_elemental.lash'},
        ]},
    },
    'tags': TRAITS,
    'authoring_description': (
        'A fantasy elemental made from bromine (Br, atomic number 35). Its glossy '
        'red-brown liquid forms a face, flowing arms and a pool. Translucent reddish '
        'vapor rises from the liquid. It has no clothing, armor or mechanical parts. '
        'The vapor color and the liquid color are inspired by bromine, not fire.'),
    'gameplay_description': (
        'A ground-based enemy that flows along the floor. It gathers its liquid '
        'before a wide forward lash. On defeat its body collapses into a puddle. '
        'It turns through a front view while its liquid mass settles. '
        'The vapor is part of its animation and has no separate damage area.'),
}

EDGE = '#35151d'
SHADOW = '#631e25'
BASE = '#7d231f'
MID = '#a83b2c'
LIGHT = '#cf6941'
GLINT = '#f4b78a'
FACE = '#32131c'
EYE = '#ffdbad'
VAPOR_DARK = '#8c5b53'
VAPOR_MID = '#b27a6b'
VAPOR_LIGHT = '#d8b8aa'


@dataclass(frozen=True)
class Pose:
    cycle: float = 0.
    move: float = 0.
    ready: float = 0.
    strike: float = 0.
    recover: float = 0.
    notice: float = 0.
    hurt: float = 0.
    death: float = 0.
    view: float = 1.
    face_view: float = 1.
    arm_view: float = 1.
    turn_slush: float = 0.


def pose(anim, i, n):
    t = phase(i, n, anim in LOOPS)
    p = math.tau * (t % 1.)
    if anim == 'idle':
        return Pose(p)
    if anim in ('walk', 'run'):
        return Pose(p, move=.65 if anim == 'walk' else 1.)
    if anim == 'turnaround':
        # The engine draws the row in the new facing. Turn from the old
        # three-quarter view through the front to the new view.
        slush = math.sin(math.pi*t) if 0 < t < 1 else 0.
        def yaw(u):
            u = max(0., min(1., u))
            if u == 0. or u == 1.:
                return 2*u-1
            return math.sin(TURN_ANGLE*(2*u-1))/math.sin(TURN_ANGLE)
        return Pose(cycle=.55*slush, view=yaw(t),
                    face_view=yaw(t+.09*slush), arm_view=yaw(t-.09*slush),
                    turn_slush=slush)
    if anim == 'notice':
        return Pose(p, notice=track(t, [(0, 0), (.45, 1), (1, .3)]))
    if anim == 'windup':
        return Pose(p, ready=track(t, [(0, 0), (.82, 1), (1, 1)]))
    if anim == 'attack_side':
        # Use the same pose at the end of windup and the active boundary.
        flow = t/A if t <= A else 1 + (t-A)/(1-A)
        return Pose(math.tau*(flow % 1.),
                    ready=track(t, [(0, 0), (.82*A, 1), (A, 1), (A+.045, 0), (1, 0)]),
                    strike=track(t, [(0, 0), (A, 0), (A+.04, 1), (B, 1), (B+.13, .1), (1, 0)]),
                    recover=track(t, [(0, 0), (B, 0), (B+.16, 1), (1, 0)]))
    if anim == 'hit':
        return Pose(p, hurt=math.sin(math.pi*t))
    if anim in ('death', 'death_idle'):
        d = 1. if anim == 'death_idle' else track(t, [(0, 0), (.13, .04), (.82, 1), (1, 1)])
        return Pose(death=d)
    raise ValueError(anim)


def _transform(q):
    p, d = q.cycle, q.death
    breath = .028*math.cos(p)*(1-d)
    width = 1 + .18*q.move + .11*q.ready + .12*q.recover + .11*q.hurt + .24*d + .07*q.turn_slush + breath
    height = (1 - .15*q.move + .15*q.ready - .14*q.strike - .18*q.recover
              + .06*q.notice - .15*q.hurt - .055*q.turn_slush)*(1-.90*d)/(1+breath)

    def P(x, y):
        u = max(0., min(1., -y/145.))
        bend = (16*q.move - 20*q.ready + 11*q.strike - 13*q.hurt - 8*q.recover)*u
        wave = (4.0+9*q.move)*math.sin(p-y*.039)*u*(1-d)
        ripple = (1-u)**3 * 3*math.sin(p*q.view-x*.04)*(1-d)
        center = PIVOT_X+(CX-PIVOT_X)*q.view
        return center+x*width+(bend+wave)*q.view+ripple, GROUND+y*height

    return P


def _vapor(c, P, q):
    """Draw rising, spreading folds of translucent vapor behind the liquid."""
    p, d = q.cycle, q.death
    x0, y0 = P(3*q.view, -141)
    # The cloud source follows the head down when the liquid collapses.
    strength = (1-.78*d)*(1+.16*q.strike+.22*q.ready)
    drift = (15*q.move + 10*q.strike - 5*q.recover)*q.view - 12*q.turn_slush
    gas = Canvas(FRAME_SIZE, super_scale=c.s)
    # Draw dense vapor near the source, then lower-density rolls farther out.
    # The gas is not attached to a rigid limb. It keeps its own flow during a turn.
    def S(x, y):
        return x0+strength*(x-drift*.3+4*math.sin(p+y*.05)*q.view), y0+strength*y
    alpha = round(154*(1-.68*d))
    shape(gas, S, (-34,15), [((-54,4),(-53,-19),(-37,-30)),
          ((-41,-51),(-18,-64),(0,-57)),
          ((18,-64),(41,-51),(37,-30)),
          ((53,-19),(54,4),(34,15)),
          ((20,23),(7,14),(0,14)),
          ((-7,14),(-20,23),(-34,15))], (117,74,67,alpha))
    shape(gas, S, (-24,3), [((-29,-14),(-14,-30),(0,-28)),
          ((14,-30),(29,-14),(24,3)),
          ((17,16),(6,16),(0,12)),
          ((-6,16),(-17,16),(-24,3))], (150,98,85,round(alpha*.72)))
    # The paired rolls widen instead of narrowing at the front view.
    for j in range(3):
        f = (p/math.tau + j/3) % 1.
        life = math.sin(math.pi*f)**.65
        if life < .04:
            continue
        rx = (17+20*f)*strength*life
        ry = (11+9*f)*strength*life
        a = round((158-66*f)*life*(1-.44*d))
        for side in (-1,1):
            x = x0+side*(10+27*f)*strength + 11*math.sin(2.6*f+j)*q.view-drift*f
            y = y0-3-48*f*strength+side*q.view*3*math.sin(j+f*2)
            def V(vx, vy):
                return x+vx*rx, y+vy*ry
            puff = Canvas(FRAME_SIZE, super_scale=c.s)
            shape(puff, V, (0,-.82), [((.40,-1.14),(1.07,-.70),(.97,-.29)),
                  ((1.32,.02),(1.02,.57),(.52,.55)),
                  ((.36,.82),(.13,.85),(0,.69)),
                  ((-.13,.85),(-.36,.82),(-.52,.55)),
                  ((-1.02,.57),(-1.32,.02),(-.97,-.29)),
                  ((-1.07,-.70),(-.40,-1.14),(0,-.82))], (140,102,92,a))
            shape(puff,V,(-.75,-.15),[((-.63,-.67),(-.22,-.75),(0,-.55)),
                  ((.22,-.75),(.63,-.67),(.75,-.15)),
                  ((.45,-.37),(.17,-.16),(0,-.20)),
                  ((-.17,-.16),(-.45,-.37),(-.75,-.15))], (209,179,167,round(a*.69)))
            gas.image.alpha_composite(puff.image)
    c.image.alpha_composite(gas.image)


def _drop(c, x, y, r, angle=0., light_side=1.):
    c.oval((x,y), r, r*.82, BASE, EDGE, 1.15, angle=angle)
    c.oval((x+r*.16*light_side,y+r*.12),r*.65,r*.49,SHADOW,None,angle=angle)
    c.oval((x-r*.28*light_side,y-r*.35),r*.27,r*.12,GLINT,None,angle=-25*light_side+angle)


def _reflect(point):
    return (-point[0], point[1])


def _view_outline(q, ex, ey):
    """Draw two matched contours from the front and side views.

    Each segment has the same landmark in each view. The shoulders and
    tendrils turn after the head. No frame or complete body is scaled to
    simulate yaw.
    """
    p, r = q.cycle, q.ready
    x = -69-10*r+5*math.sin(p+.7)
    y = -83-14*r+9*math.cos(p)
    # Both sides use this contour in the front view. The two curls remain
    # visible and the trunk has a broad, round cross section.
    front = [((14,-164),(28,-157),(36,-145)),
             ((49,-135),(53,-118),(49,-102)),
             ((49,-96),(49,-90),(47,-85)),
             ((63,-104),(83,-105),(90,-88)),
             ((102,-72),(89,-56),(77,-59)),
             ((64,-60),(62,-72),(71,-74)),
             ((59,-65),(48,-48),(31,-34)),
             ((16,-20),(54,-26),(76,-17)),
             ((95,-12),(96,-3),(70,0)),
             ((46,1),(24,1),(0,0))]
    near = [((-1,-162),(14,-166),(27,-155)),
            ((39,-148),(31,-141),(38,-138)),
            ((54,-125),(63,-104),(48,-88)),
            ((45,-80),(ex-24,ey-24),(ex-6,ey-17)),
            ((ex+13,ey-11),(ex+17,ey+9),(ex+4,ey+17)),
            ((ex-12,ey+29),(ex-24,ey+14),(ex-16,ey+3)),
            ((ex-34,ey+15),(35,-48),(22,-34)),
            ((9,-20),(51,-27),(75,-17)),
            ((95,-12),(95,-3),(70,0)),
            ((46,1),(23,1),(0,0))]
    far = [((-10,-151),(-16,-140),(-23,-124)),
           ((-34,-117),(-42,-113),(-42,-105)),
           ((-43,-101),(-41,-96),(-39,-96)),
           ((-55,-114),(x-9,y-27),(x-16,y-6)),
           ((x-28,y+11),(x-13,y+32),(x+7,y+23)),
           ((x+24,y+17),(x+18,y+5),(x+8,y+7)),
           ((x-6,y+20),(x+1,y-10),(-37,-65)),
           ((-32,-42),(-46,-24),(-68,-21)),
           ((-93,-14),(-96,-3),(-71,0)),
           ((-48,1),(-24,1),(0,0))]

    def half(side):
        # Interpolate corresponding control points. The far contour is not a
        # compressed near contour: it has its own shoulder, curl and pool.
        start = (5*q.view,-156+5*abs(q.view))
        segments = []
        for j, fseg in enumerate(front):
            v = q.arm_view if 3 <= j <= 6 else q.view
            facing = 1 if v >= 0 else -1
            is_near = side == facing
            authored = near[j] if is_near else far[j]
            if facing < 0:
                authored = tuple(_reflect(k) for k in authored)
            fseg = fseg if side > 0 else tuple(_reflect(k) for k in fseg)
            segments.append(tuple(mix(k,l,abs(v)) for k,l in zip(fseg,authored)))
        return path(start, *segments)

    return half(1) + list(reversed(half(-1)))


def _side_details(c, P, q, ex, ey):
    p,d,r,a = q.cycle,q.death,q.ready,q.strike
    x = -69 - 10*r + 5*math.sin(p+.7)
    y = -83 - 14*r + 9*math.cos(p)
    shape(c,P,(-39,-96),[((-55,-114),(x-9,y-27),(x-16,y-6)),
          ((x-28,y+11),(x-13,y+32),(x+7,y+23)),
          ((x+24,y+17),(x+18,y+5),(x+8,y+7)),
          ((x+1,y+13),(x-6,y+7),(x-3,y-2)),
          ((x+4,y-14),(-37,-77),(-39,-96))],SHADOW)
    if d < .91:
        stroke(c,P,(x-11,y-4),[((x-16,y-13),(x-4,y-18),(x+2,y-12))],LIGHT,2.7)
    # Dark folds and reflected light describe liquid surface curvature.
    shape(c,P,(-37,-110),[((-17,-125),(4,-120),(7,-108)),
          ((11,-88),(-17,-80),(-11,-55)),
          ((-6,-34),(-23,-16),(-56,-14)),
          ((-21,-6),(4,-13),(11,-30)),
          ((36,-62),(42,-77),(45,-100)),
          ((44,-127),(8,-155),(-18,-138)),
          ((-33,-130),(-34,-121),(-37,-110))],SHADOW)
    shape(c,P,(-21,-127),[((-13,-144),(12,-151),(30,-139)),
          ((9,-142),(-5,-129),(-9,-114)),
          ((-17,-105),(-24,-112),(-21,-127))],MID)
    shape(c,P,(-34,-85),[((-20,-72),(-26,-51),(-34,-36)),
          ((-41,-23),(-59,-19),(-71,-13)),
          ((-48,-15),(-15,-24),(-16,-49)),
          ((-13,-63),(-21,-83),(-34,-85))],MID)
    shape(c,P,(29,-69),[((42,-79),(ex-15,ey-23),(ex-3,ey-13)),
          ((ex-17,ey-15),(ex-35,ey-8),(36,-54)),
          ((29,-51),(24,-56),(29,-69))],MID)
    shape(c,P,(-66,-8),[((-37,-4),(-12,-16),(15,-13)),
          ((38,-12),(55,-17),(73,-10)),
          ((60,-2),(-28,-3),(-66,-8))],MID)
    if d < .91:
        stroke(c,P,(-11,-141),[((0,-149),(19,-146),(29,-140))],GLINT,2.8)
        stroke(c,P,(-33,-101),[((-41,-90),(-35,-79),(-31,-74))],LIGHT,3.)
        stroke(c,P,(-38,-37),[((-46,-24),(-55,-25),(-61,-22))],LIGHT,2.4)
        stroke(c,P,(ex-18,ey-15),[((ex-9,ey-18),(ex+4,ey-13),(ex+7,ey-7))],GLINT,2.5)
        stroke(c,P,(25,-18),[((41,-20),(52,-19),(65,-15))],LIGHT,2.2)
        stroke(c,P,(-4,-148),[((5,-144),(12,-135),(11,-124))],GLINT,1.9)



def _front_details(c, P, q):
    # The two front folds are visible together. At a side view the far fold
    # falls behind the body and the near curl carries the highlight.
    shape(c,P,(0,-144),[((24,-144),(40,-132),(37,-112)),
          ((35,-93),(17,-80),(18,-55)),
          ((18,-33),(34,-19),(52,-13)),
          ((19,-5),(-19,-5),(-52,-13)),
          ((-34,-19),(-18,-33),(-18,-55)),
          ((-17,-80),(-35,-93),(-37,-112)),
          ((-40,-132),(-24,-144),(0,-144))],SHADOW)
    for side in (-1,1):
        def F(x,y):
            return P(side*x,y)
        shape(c,F,(17,-139),[((39,-134),(48,-114),(42,-100)),
              ((35,-90),(29,-74),(27,-55)),
              ((26,-37),(38,-24),(56,-17)),
              ((33,-18),(13,-37),(13,-57)),
              ((11,-82),(34,-108),(27,-127)),
              ((25,-133),(20,-135),(17,-139))],MID)
        shape(c,F,(47,-88),[((63,-104),(81,-102),(88,-86)),
              ((77,-91),(65,-91),(58,-80)),
              ((54,-74),(51,-69),(44,-66)),
              ((40,-74),(43,-81),(47,-88))],MID)
        if q.death < .91:
            stroke(c,F,(17,-147),[((30,-145),(39,-138),(41,-129))],GLINT,2.5)
            stroke(c,F,(36,-62),[((34,-43),(42,-29),(55,-23))],LIGHT,2.6)
            stroke(c,F,(67,-95),[((76,-97),(84,-94),(88,-87))],GLINT,2.5)
    shape(c,P,(-67,-8),[((-38,-6),(-20,-13),(0,-13)),
          ((20,-13),(38,-6),(67,-8)),
          ((40,-2),(-40,-2),(-67,-8))],MID)


def _composite_details(dest, layer, mask, weight):
    if weight <= 0:
        return
    alpha = ImageChops.multiply(layer.image.getchannel('A'), mask)
    if weight < 1:
        alpha = alpha.point(lambda a: round(a*weight))
    layer.image.putalpha(alpha)
    dest.image.alpha_composite(layer.image)


def _face(c, P, q):
    if q.death >= .60:
        return
    # Draw the face in its own view. Both eyes stay on the curved surface;
    # the far eye is narrower in a three-quarter view.
    u = abs(q.face_view)
    side = 1 if q.face_view >= 0 else -1
    def F(x,y):
        return P(side*x,y)
    front_start = (-34,-119)
    front = [((-23,-133),(-12,-135),(0,-135)),
             ((12,-135),(23,-133),(34,-119)),
             ((43,-104),(30,-90),(17,-82)),
             ((10,-77),(5,-75),(0,-75)),
             ((-5,-75),(-10,-77),(-17,-82)),
             ((-30,-90),(-43,-104),(-34,-119))]
    side_start = (-13,-120)
    profile = [((-3,-131),(15,-134),(27,-130)),
               ((37,-129),(44,-122),(46,-113)),
               ((56,-98),(40,-88),(24,-79)),
               ((17,-74),(13,-76),(9,-83)),
               ((6,-88),(0,-90),(-4,-92)),
               ((-17,-100),(-23,-111),(-13,-120))]
    segments = [tuple(mix(a,b,u) for a,b in zip(f,s)) for f,s in zip(front,profile)]
    shape(c,F,mix(front_start,side_start,u),segments,FACE)
    k = 1-.76*q.hurt
    for eye,xf,xs,yf,ys,wf,ws in [(-1,-17,7,-111,-110,11,10),(1,17,34,-111,-111,11,8)]:
        x=xf+(xs-xf)*u; y=yf+(ys-yf)*u; w=wf+(ws-wf)*u
        tilt=3.5+2.5*q.ready+1.8*q.strike
        # The left eye slopes down toward the nose. The opposite eye uses
        # the same authored curve in its own local coordinates.
        def E(a,b):
            return F(x-eye*a,y+b)
        shape(c,E,(-w,-3*k-tilt),[((-3,-4*k-tilt),(3,-3*k+tilt),(w,tilt)),
              ((w-3,6*k+tilt),(-2,8*k),(-w,-3*k-tilt))],EYE)
    mx=24*u
    if q.hurt > .3:
        c.oval(F(mx,-92),3.2,4.1,'#a34c43',None)
    else:
        stroke(c,F,(mx-7,-92),[((mx-3,-97),(mx+3,-97),(mx+7+u,-92-2*u))],SHADOW,1.4)


def _paint(c, q):
    p, d, r, a = q.cycle, q.death, q.ready, q.strike
    P = _transform(q)
    _vapor(c, P, q)
    ex = 58 + 92*a - 31*r + 3*math.sin(p+.4)*(1-a) - 10*q.recover
    ey = -76 - 22*r + 21*a + 5*math.cos(p+.6)*(1-a)
    outline = [P(*v) for v in _view_outline(q,ex,ey)]
    liquid = Canvas(FRAME_SIZE,super_scale=c.s)
    liquid.poly(outline,BASE,None)
    mask = liquid.image.getchannel('A')
    if abs(q.view) < 1.:
        front = Canvas(FRAME_SIZE,super_scale=c.s)
        _front_details(front,P,q)
        _composite_details(liquid,front,mask,1-abs(q.view))
    if abs(q.view) > 0.:
        side = Canvas(FRAME_SIZE,super_scale=c.s)
        facing = 1 if q.view >= 0 else -1
        _side_details(side,lambda x,y: P(facing*x,y),q,ex,ey)
        _composite_details(liquid,side,mask,abs(q.view))
    _face(liquid,P,q)
    liquid.line(outline,EDGE,2.2,closed=True)
    # Project each droplet from its orbit. Draw the rear droplets before
    # the liquid so the silhouette occludes part of a drop, not all of it.
    drops = []
    if d < 1.:
        yaw = math.asin(max(-1.,min(1.,q.view*math.sin(TURN_ANGLE))))
        for j in range(2):
            f = (p/math.tau+.25+j*.5) % 1.
            life = math.sin(math.pi*f)**.7*(1-d)
            if life < .08:
                continue
            for side in (-1,1):
                azimuth = side*(1.45+j*1.52+p*.65)+yaw
                x = (65+8*math.sin(math.pi*f))*math.sin(azimuth)
                z = math.cos(azimuth)
                y = -41-63*math.sin(math.pi*f)+7*z
                xx,yy = P(x,y)
                radius = (3.5+2.2*j)*life*(.87+.13*z)
                drops.append((z,xx,yy,radius,24*math.sin(azimuth)))
    drops.sort()
    for z,x,y,radius,angle in drops:
        if z < 0:
            _drop(c,x,y,radius,angle,q.view)
    c.image.alpha_composite(liquid.image)
    for z,x,y,radius,angle in drops:
        if z >= 0:
            _drop(c,x,y,radius,angle,q.view)
    # A defeated creature leaves real liquid, not a baked contact shadow.
    if d > .22:
        u = (d-.22)/.78
        for side, x, size in [(-1,101,6),(1,105,7),(-1,119,3),(1,128,4)]:
            xx = CX+side*(53+(x-53)*u)
            yy = GROUND-size-30*4*u*(1-u)
            _drop(c,xx,yy,size*u,side*15)
        if u > .20:
            puddle = lambda x, y: (CX+x, GROUND+y)
            stroke(c, puddle, (-46,-8), [((-16,-6),(18,-7),(54,-9))], LIGHT, 4.6*u)
            stroke(c, puddle, (-24,-5), [((-10,-4),(6,-4),(23,-5))], GLINT, 2.3*u)
            if u > .45:
                for dx, dy, rr in [(-15, -7, 2.4), (7, -6, 1.8), (29, -8, 2.0)]:
                    c.oval(puddle(dx, dy), rr*u, rr*.78*u, MID, EDGE, .8)


def _render_frame(anim, i, n):
    c = Canvas(FRAME_SIZE)
    _paint(c, pose(anim, i, n))
    return c.finish()


def _body_metrics(w, h):
    # Exclude vapor, detached drops, and the attack extension from the body.
    return body_metrics_for_box(BODY_BOX, w, h)


def render(out_dir: str | Path, **opts):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result = build_sheet(target=TARGET_NAME, rows=ROWS, render_fn=_render_frame,
                         out_dir=out_dir, frame_size=FRAME_SIZE, auto_crop=False,
                         actor_metadata=ACTOR_METADATA, body_metrics_fn=_body_metrics,
                         animation_key_map={a:a for a,_,_ in ROWS}, pose_bodies="authored")
    return [result[k] for k in ('spritesheet', 'yaml', 'ron', 'actor', 'preview',
                                'canonical', 'canonical_transparent')]
