"""Danger Elemental: a predatory hazard glyph.

Sharp graphic anatomy, hinged chevron blades and a warning-color reveal.
The engine owns movement and damage; the silhouette is not the hitbox.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

from ...core.draw import rgba
from ...chargen.geometry import clip_convex

from ._clockwork_enemy_art import Canvas, add, sub, mul, mix, lerp, rot, unit, perp, phase, track
from ._replicator_radical_art import floating_actor, publish
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'danger_elemental'
FRAME_SIZE = (340, 270)
CENTER = (153., 133.)
WINDUP, ACTIVE, RECOVER = .62, .22, .74
TOTAL = WINDUP + ACTIVE + RECOVER
A, B = WINDUP / TOTAL, (WINDUP + ACTIVE) / TOTAL
ROWS = [('idle', 24, 60), ('walk', 24, 50), ('run', 24, 40),
        ('notice', 10, 55), ('windup', 20, 31), ('attack_side', 51, 31),
        ('hit', 10, 55), ('death', 24, 55)]
LOOPS = {'idle', 'walk', 'run'}
TRAITS = ['elemental', 'danger', 'warning', 'pictogram']
ACTOR_METADATA = floating_actor(TARGET_NAME, 'Danger Elemental', 'art', TRAITS,
    'An angular predatory spirit made of warning colors, hooked hazard blades and a living ink silhouette.',
    'A floating charger. Its amber warning flares red; two hooked blades sweep forward into a spear-like strike. Graphic streaks are visual only.')
ACTOR_METADATA['body']['body_kind'] = 'Floating'
ACTOR_METADATA['body']['mass_class'] = 'Medium'
ACTOR_METADATA['actions'] = {'default_preset': 'danger_elemental_charge'}
ACTOR_METADATA['animation_bindings'].update({
    'locomotion.run': {'animation': 'run', 'events': []},
    'action.melee.primary': {'animation': 'attack_side', 'events': [
        {'t': A, 'event': 'hitbox_active_start', 'source': 'danger_elemental.charge'},
        {'t': B, 'event': 'hitbox_active_end', 'source': 'danger_elemental.charge'},
    ]},
})

INK = '#271d2a'


def color(a, b, t):
    """Interpolate two paint colors."""
    return tuple(round(v) for v in mix(rgba(a), rgba(b), t))


@dataclass(frozen=True)
class Pose:
    cycle: float = 0.
    alarm: float = 0.
    wind: float = 0.
    strike: float = 0.
    lean: float = 0.
    x: float = 0.
    y: float = 0.
    motion: float = 0.
    hurt: float = 0.
    death: float = 0.


def pose(anim, i, n):
    t = phase(i, n, anim in LOOPS)
    p = math.tau * (t % 1.)
    if anim in LOOPS:
        speed = {'idle': 0., 'walk': .55, 'run': 1.}[anim]
        return Pose(p, lean=8*speed+2.8*math.sin(p), y=3.5*math.sin(p), motion=speed)
    if anim == 'notice':
        a = track(t, [(0,0),(.45,.65),(1,.7)])
        return Pose(alarm=a, lean=-8*a, y=-5*a)
    if anim == 'windup':
        u = track(t, [(0,0),(.72,.90),(1,1)])
        return Pose(alarm=u, wind=u, lean=-19*u, x=-5*u, y=4*u)
    if anim == 'attack_side':
        # Align the visual strike with the first active sample.
        launch = A - .085 / TOTAL
        wind = track(t, [(0,0),(launch,1),(A,0),(1,0)])
        strike = track(t, [(0,0),(launch,0),(A,1),(B,1),(B+.12,.30),(1,0)])
        alarm = track(t, [(0,0),(launch,1),(B+.12,1),(1,0)])
        tilt = track(t, [(0,0),(launch,-19),(A,73),(B,73),(B+.18,12),(1,0)])
        return Pose(alarm=alarm, wind=wind, strike=strike, lean=tilt,
                    x=-5*wind+5*strike, y=4*wind-3*strike, motion=strike)
    if anim == 'hit':
        h = math.sin(math.pi*t)
        return Pose(alarm=.65*h, lean=-24*h, x=-8*h, y=4*h, hurt=h)
    if anim == 'death':
        d = track(t, [(0,0),(.12,.04),(.85,1),(1,1)])
        return Pose(death=d)
    raise ValueError(anim)


def polygon(c, P, pts, fill, edge=INK, width=2.4):
    c.poly([P(*v) for v in pts], fill, edge, width)


def line(c, P, pts, fill, width=1.5):
    c.line([P(*v) for v in pts], fill, width)


def paints(q):
    a=q.alarm
    return dict(edge='#1d1922', dark='#3b303c', middle='#5b4145',
                warm=color('#df8c30','#b42f34',a),
                vivid=color('#f8be43','#f04439',a),
                light=color('#ffe289','#ff9e76',a),
                shine=color('#fff2be','#ffe7b6',a),
                red=color('#a8492d','#7a2536',a),
                shadow=color('#8d582e','#8c2934',a))


def _stripe_panel(c, P, left, right, q, pal, far=False):
    """A striped bevel along a blade; adjacent bands share exact boundaries.

    A longitudinal shear gives diagonal stripes without extending beyond
    the quadrilateral. The rest of the blade is a separately shaded facet.
    """
    def at(t,u):
        return mix(mix(left[0],left[1],t),mix(right[0],right[1],t),u)
    # Clip the stripe in the unit parameter rectangle using chargen's
    # existing convex clipper, then map into the blade's tapered bevel.
    panel=[(0.,0.),(1.,0.),(1.,1.),(0.,1.)]
    polygon(c,P,[left[0],left[1],right[1],right[0]],pal['vivid'],None)
    for k in range(-1,5):
        lo=k*.29+.07; hi=lo+.125; shift=.16
        strip=clip_convex([(lo,0.),(hi,0.),(hi+shift,1.),(lo+shift,1.)],panel)
        if len(strip)>=3:
            polygon(c,P,[at(t,u) for t,u in strip],pal['dark'] if far else pal['edge'],None)
    line(c,P,[left[0],left[1]],pal['light'],1.6)
    line(c,P,[right[0],right[1]],pal['shadow'],1.8)


def _blade(c, R, root, hinge, angle, size, q, pal, far=False):
    """Hooked, articulated graphic blade, separate from the body rotation."""
    def H(x,y):return add(hinge,rot((x*size,y*size),angle))
    # Tapered arm and high-contrast underside rather than a dangling ribbon.
    v=unit(sub(hinge,root)); n=perp(v)
    arm=[add(root,mul(n,-13)),add(hinge,mul(n,-17)),
         add(hinge,mul(n,14)),add(root,mul(n,10))]
    polygon(c,R,arm,pal['dark'],pal['edge'],2.8)
    polygon(c,R,[arm[0],arm[1],add(hinge,mul(n,-6)),add(root,mul(n,-3))],pal['warm'],None)
    # Long leading edge, notch and swept-back secondary hook.
    outline=[(-12,-18),(12,-27),(35,-23),(68,-8),(88,9),(51,8),
             (41,21),(23,12),(6,36),(-6,20),(-22,6)]
    def P(x,y):return R(*H(x,y))
    polygon(c,P,outline,pal['edge'],pal['edge'],3.2)
    polygon(c,P,[(-11,-16),(12,-24),(34,-20),(66,-6),(82,6),(48,4),(39,16),(23,8),(6,31),(-4,16),(-18,5)],pal['warm'],None)
    # The dark underside forms the hook; keep large uninterrupted facets.
    polygon(c,P,[(-18,5),(6,31),(23,8),(39,16),(48,4),(82,6),(34,-9),(8,1)],pal['dark'],None)
    _stripe_panel(c,P,((12,-24),(66,-6)),((8,1),(48,4)),q,pal,far)
    polygon(c,P,[(-11,-16),(12,-24),(8,1),(-18,5)],pal['light'],None)
    line(c,P,[(12,-24),(34,-20),(66,-6),(82,6)],pal['shine'],2.0)
    line(c,P,[(6,31),(23,8),(39,16)],pal['red'],2.2)
    line(c,P,[(48,4),(82,6)],pal['light'],1.7)
    polygon(c,P,[(68,-6),(82,6),(63,1)],pal['shine'],None)
    polygon(c,P,[(22,6),(37,10),(40,5),(32,2)],pal['red'],None)
    # A little irregular chip at the lower edge reinforces the hazard motif.
    line(c,P,[(-11,-12),(-6,-5),(-10,0)],pal['shadow'],1.4)


def _body(c,P,q,pal):
    a,h,w=q.alarm,q.strike,q.wind
    # A tapering, jagged ink silhouette: no flat sign or enclosing frame.
    # Shoulders and crown form the implied warning triangle, not a road sign.
    outer=[(-53,-29),(-38,-37),(-31,-55),(-12,-45),(1,-76),(13,-57),
           (30,-45),(50,-54),(49,-30),(65,-15),(53,11),(39,20),(32,43),
           (9,69),(-1,48),(-23,60),(-15,34),(-41,26),(-56,7),(-64,-8)]
    polygon(c,P,outer,pal['edge'],pal['edge'],3.2)
    # Side planes, face cavity and the swept underside are large color masses.
    polygon(c,P,[(-51,-24),(-29,-48),(-11,-37),(1,-68),(15,-49),(32,-37),(46,-46),(45,-22),(57,-12),(42,9),(18,1),(-17,6),(-44,4)],pal['vivid'],None)
    polygon(c,P,[(-51,-24),(-29,-48),(-24,-28),(-38,-11),(-44,4),(-55,-8)],pal['shadow'],None)
    polygon(c,P,[(1,-68),(15,-49),(32,-37),(24,-29),(5,-41),(-5,-33)],pal['light'],None)
    polygon(c,P,[(1,-68),(-5,-33),(-11,-37),(-29,-48),(-12,-29)],pal['warm'],None)
    line(c,P,[(1,-65),(4,-51),(13,-43)],pal['shine'],1.35)
    polygon(c,P,[(46,-46),(45,-22),(57,-12),(42,9),(35,-8),(31,-27)],pal['red'],None)
    polygon(c,P,[(-55,-8),(-44,4),(-36,15),(-40,21),(-52,8)],pal['warm'],None)
    polygon(c,P,[(57,-12),(54,8),(39,20),(30,28),(37,16),(42,9)],pal['shadow'],None)
    # A deep, cut-paper face with raised brows. Eyes are not printed icons.
    mask=[(-37,-14),(-24,-30),(-5,-20),(8,-23),(26,-30),(43,-16),
          (38,7),(24,18),(3,20),(-19,15),(-36,5)]
    polygon(c,P,mask,pal['dark'],pal['edge'],1.9)
    polygon(c,P,[(-37,-14),(-24,-30),(-5,-20),(8,-23),(26,-30),(43,-16),
                 (28,-17),(11,-9),(-6,-11),(-23,-19)],pal['middle'],None)
    # Recessed angular eyes; expand the lower lids as the attack fires.
    blink=1-.91*max(0,1-abs(q.cycle/math.tau-.79)/.05) if q.cycle else 1.
    k=(1-.55*q.hurt)*blink
    for side in (-1,1):
        def E(x,y):return P(side*x+3,y)
        eye=[(5,-7),(26,-15-3*a),(23,-5+5*k),(11,0+5*k)]
        polygon(c,E,eye,pal['edge'],None)
        if k>.18:
            polygon(c,E,[(7,-6),(24,-12-3*a),(21,-5+4*k),(11,-1+3*k)],pal['shine'],None)
            polygon(c,E,[(12,-6),(15,-7),(16,-1+3*k),(13,1)],color('#b75630','#f04439',a),None)
        line(c,E,[(5,-10),(25,-17-3*a)],pal['light'],2.8)
    # The lower face opens into a serrated grin, like a torn hazard glyph.
    mouth=track(h,[(0,.0),(1,1.)]); my=16+3*mouth
    polygon(c,P,[(-24,10),(-10,14),(5,12),(22,6),(19,my+10*mouth),
                  (3,my+8*mouth),(-13,my+5*mouth)],pal['edge'],None)
    for j in range(4):
        x=-17+j*9
        y=13-abs(x-1)*.12
        polygon(c,P,[(x-3,y),(x+4,y-1),(x+1,y+5+4*mouth)],pal['shine'],None)
    # Split, tapering torso with an elongated luminous exclamation mark in
    # negative space; it reads as a warning rune, not the character's face.
    polygon(c,P,[(-40,21),(-22,28),(-8,23),(13,24),(37,16),(28,39),(10,60),(0,41),(-18,51),(-12,29)],pal['middle'],None)
    polygon(c,P,[(-34,21),(-22,28),(-13,31),(-18,48),(-31,30)],pal['red'],None)
    polygon(c,P,[(13,24),(37,16),(28,39),(10,60),(16,35)],pal['warm'],None)
    polygon(c,P,[(-6,24),(8,24),(4,39),(-3,40)],pal['light'],None)
    polygon(c,P,[(-4,44),(3,43),(5,48),(0,52),(-5,49)],pal['shine'],None)
    line(c,P,[(-50,-24),(-29,-48),(-11,-37),(1,-68),(15,-49)],pal['shine'],2.0)
    line(c,P,[(32,-37),(46,-46),(45,-22)],pal['light'],1.6)
    line(c,P,[(28,39),(10,60)],pal['light'],1.5)
    line(c,P,[(-40,21),(-22,28),(-18,48)],pal['warm'],1.7)
    polygon(c,P,[(18,30),(27,24),(22,37),(12,48)],pal['light'],None)
    line(c,P,[(-24,10),(-10,14),(5,12),(22,6)],pal['shadow'],1.6)


def _draw_alive(c,q):
    p=q.cycle; a=q.alarm; w=q.wind; h=q.strike
    pal=paints(q)
    origin=add(CENTER,(q.x,q.y))
    # Head and trunk bank into a charge, but retain a recognizable face.
    lean=q.lean*.61
    def P(x,y):return add(origin,rot((x*(1+.09*w),y*(1-.07*w)),lean))
    def R(x,y):return add(origin,(x,y))
    f=math.sin(p); g=math.cos(p); drift=q.motion*(1-h)
    # A small swept blade/tail, behind the body. The broad facets are an
    # extension of the ink shape rather than a third sign.
    tail=[(-15,34),(-40-24*h,48),(-72-36*h-6*drift,44+8*f),
          (-44-20*h,68+8*g),(-75-21*h,84+5*f),(-21,71),(5,48)]
    polygon(c,R,tail,pal['dark'],pal['edge'],2.6)
    polygon(c,R,[tail[0],tail[1],tail[2],tail[3],(-31,58)],pal['red'],None)
    line(c,R,[tail[2],tail[3],tail[4]],pal['warm'],2.2)
    polygon(c,R,[tail[3],tail[4],tail[5],(-20,62)],pal['middle'],None)
    # The two blades are hinged near the shoulders. They flare backward
    # during anticipation, then sweep in front like a raptor's talons.
    far_root=sub(P(-35,-8),origin); near_root=sub(P(38,7),origin)
    far_hinge=mix((-45-8*w, -9-12*w+5*f),(8,-36),h)
    far_angle=lerp(-155-27*w+7*f,-24,h)
    _blade(c,R,far_root,far_hinge,far_angle,.86,q,pal,True)
    # Raised warning chevrons take the place of simplistic radial lines.
    if a>.12 and h<.72:
        for j,(x,y) in enumerate([(-37,-82),(1,-101),(40,-83)]):
            k=(.65+.35*a)*(1-h)
            pts=[(x-6*k,y+10*k),(x,y-3*k),(x+6*k,y+10*k),(x,y+5*k)]
            polygon(c,R,pts,pal['light'],None)
    _body(c,P,q,pal)
    near_hinge=mix((50+10*w,24+6*f+3*w),(51,27),h)
    near_angle=lerp(30+36*w+8*g,-12,h)
    _blade(c,R,near_root,near_hinge,near_angle,1.,q,pal)
    if h>.12:
        # Short graphic motion trails, progressively thinner and darker.
        for j,(dx,dy) in enumerate([(-65,-49),(-86,-20),(-79,18),(-61,55)]):
            x,y=dx-12*h,dy
            span=(13+7*(j%2))*h
            polygon(c,R,[(x-span,y+3),(x+4,y),(x-span*.65,y-3)],pal['warm'],None)
            line(c,R,[(x-span*.6,y),(x+3,y)],pal['light'],1.3)


def _draw_death(c,q):
    d=q.death
    if d>=1:return
    if d<.20:
        _draw_alive(c,Pose(alarm=track(d,[(0,0),(.12,1),(.2,1)]),hurt=d*3,lean=-16*d))
        return
    u=(d-.20)/.80
    pal=paints(Pose(alarm=1.))
    # Fracture the actual visual vocabulary into sharp ink and enamel
    # fragments; the actor vanishes according to the existing death policy.
    pieces=[[(0,-70),(15,-48),(-9,-27),(-29,-47)],
            [(-37,-14),(-23,-27),(-9,-12),(-14,10),(-34,4)],
            [(13,-27),(42,-16),(36,8),(18,17),(4,5)],
            [(-22,28),(7,24),(30,18),(10,62),(-12,46)],
            [(-52,-10),(-108,-39),(-93,-10),(-56,9)],
            [(47,20),(125,58),(83,62),(63,45)]]
    for j,pts in enumerate(pieces):
        mx=sum(x for x,y in pts)/len(pts);my=sum(y for x,y in pts)/len(pts)
        dst=add(CENTER,(mx+(j-2.5)*9*u,my-17*u+57*u*u))
        def F(x,y):return add(dst,rot((x-mx,y-my),(-30+j*14)*u))
        polygon(c,F,pts,pal['dark'],pal['edge'],2.8)
        polygon(c,F,[mix((mx,my),v,.74) for v in pts],pal['red'] if j%2 else pal['vivid'],None)
        line(c,F,pts[:2],pal['light'],1.6)
    for j in range(7):
        x,y=rot((42+52*u,0),-160+j*49)
        y+=48*u*u
        k=3.5*(1-u)
        polygon(c,lambda x,y:add(CENTER,(x,y)),[(x-k,y),(x,y-k),(x+k,y),(x,y+k)],pal['light'],None)


def _render_frame(anim,i,n):
    q=pose(anim,i,n)
    c=Canvas(FRAME_SIZE)
    if q.death>0: _draw_death(c,q)
    else: _draw_alive(c,q)
    im=c.finish()
    if q.death>.20:
        opacity=1-track(q.death,[(.20,0),(.45,0),(1,1)])
        im.putalpha(im.getchannel('A').point(lambda v:round(v*opacity)))
    return im


def _body_metrics(w,h):
    # Preserve the prior gameplay body box; exclude blade tips, tail, and streaks.
    return body_metrics_for_box((83,56,223,187),w,h)


def render(out_dir: str | Path, **opts):
    return publish(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA,
                   _body_metrics, out_dir, **opts)
