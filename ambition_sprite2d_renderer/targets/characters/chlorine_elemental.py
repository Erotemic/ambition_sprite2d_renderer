"""Chlorine Elemental: a dense yellow-green cloud close to the ground.

Chlorine (Cl, 17) is a yellow-green gas at room temperature. Its greater
density than air informs the low cloud. The face and combat poses are fiction.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from ._clockwork_enemy_art import Canvas, phase, track
from ._elemental_enemy_family import shape
from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'chlorine_elemental'
DISPLAY_NAME = 'Chlorine Elemental'
FRAME_SIZE = (360, 264)
BODY_BOX = (126, 76, 234, 239)
CX, GROUND = (BODY_BOX[0] + BODY_BOX[2] - 1) / 2, 237.
YAW = math.radians(46)
WINDUP_S, ACTIVE_S, RECOVER_S = .66, .24, .78
TOTAL_S = WINDUP_S + ACTIVE_S + RECOVER_S
A, B = WINDUP_S / TOTAL_S, (WINDUP_S + ACTIVE_S) / TOTAL_S
ROWS = [('idle', 24, 60), ('walk', 24, 50), ('run', 24, 36),
        ('turnaround', 11, 20), ('notice', 9, 60), ('windup', 20, 33),
        ('attack_side', 51, 33), ('hit', 9, 60), ('death', 26, 55),
        ('death_idle', 1, 200)]
LOOPS = {'idle', 'walk', 'run', 'death_idle'}
TRAITS = ['enemy', 'science', 'elemental', 'chemical_element', 'chlorine',
          'halogen', 'gas', 'no_hands']
ACTOR_METADATA = {
    'actor': {'character_id': TARGET_NAME, 'display_name': DISPLAY_NAME},
    'body': {'body_plan': 'Crawler', 'body_kind': 'Standard',
             'mass_class': 'Light', 'locomotion_hint': 'Slither', 'traits': TRAITS},
    'capabilities': {'traversal': {'walk': True}},
    'actions': {'default_preset': 'chlorine_elemental_surge'},
    'visual': {'default_pose': 'idle', 'portrait': {'animation': 'idle', 'frame': 0}},
    'animation_bindings': {
        'default': {'animation': 'idle', 'events': []},
        'locomotion.walk': {'animation': 'walk', 'events': []},
        'locomotion.run': {'animation': 'run', 'events': []},
        'combat.hurt': {'animation': 'hit', 'events': []},
        'combat.death': {'animation': 'death', 'events': []},
        'action.melee.primary': {'animation': 'attack_side', 'events': [
            {'t': A, 'event': 'hitbox_active_start', 'source': 'chlorine_elemental.surge'},
            {'t': B, 'event': 'hitbox_active_end', 'source': 'chlorine_elemental.surge'},
        ]},
    },
    'tags': TRAITS,
    'authoring_description': ('A fantasy elemental made of chlorine gas. Overlapping yellow-green '
        'gas volumes form a low cloud with eyes in its dense center. Translucent '
        'wisps spread close to the ground. It has no solid parts.'),
    'gameplay_description': ('A ground-based enemy that gathers its cloud before '
        'a forward surge. Its vapor disperses on defeat. The peripheral vapor '
        'is visual only and does not have a separate damage area.'),
}

DEEP = (43, 55, 22)
SHADOW = (80, 99, 35)
BASE = (138, 160, 55)
MID = (181, 201, 77)
LIGHT = (219, 232, 128)


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
    yaw: float = YAW
    mantle_yaw: float = YAW


def pose(anim, i, n):
    t = phase(i, n, anim in LOOPS)
    p = math.tau * (t % 1.)
    if anim == 'idle':
        return Pose(cycle=p)
    if anim in ('walk', 'run'):
        return Pose(cycle=p, move=.62 if anim == 'walk' else 1.)
    if anim == 'turnaround':
        s = math.sin(math.pi*t) if 0 < t < 1 else 0.
        return Pose(cycle=.7*s, yaw=YAW*(2*t-1),
                    mantle_yaw=YAW*(2*t-1-.16*s))
    if anim == 'notice':
        return Pose(cycle=p, notice=track(t, [(0,0),(.45,1),(1,.25)]))
    if anim == 'windup':
        return Pose(cycle=p, ready=track(t, [(0,0),(.78,1),(1,1)]))
    if anim == 'attack_side':
        flow = t/A if t <= A else 1 + (t-A)/(1-A)
        return Pose(cycle=math.tau*(flow % 1.),
                    ready=track(t, [(0,0),(.78*A,1),(A,1),(A+.045,0),(1,0)]),
                    strike=track(t, [(0,0),(A,0),(A+.045,1),(B,1),(B+.15,.12),(1,0)]),
                    recover=track(t, [(0,0),(B,0),(B+.17,1),(1,0)]))
    if anim == 'hit':
        return Pose(cycle=p, hurt=math.sin(math.pi*t))
    if anim in ('death', 'death_idle'):
        d = 1. if anim == 'death_idle' else track(t, [(0,0),(.15,.07),(.80,.85),(1,1)])
        return Pose(death=d, cycle=p if anim == 'death' else 0.)
    raise ValueError(anim)


def _clamp(x, lo=0., hi=1.):
    return max(lo, min(hi, x))


def _rgba(color, alpha):
    return (*color, round(_clamp(alpha)*255))


def _mix(a, b, t):
    return tuple(round(x+(y-x)*t) for x, y in zip(a,b))


def _project(q, x, y, z):
    """Project gas volumes. Low volumes spread along the ground."""
    a, p, d = q.mantle_yaw, q.cycle, q.death
    co, si = math.cos(a), math.sin(a)
    u = _clamp(-y/155.)
    # The upper cloud lags behind the front when it changes shape.
    width = 1+.13*q.move-.12*q.ready+.10*q.recover+.16*d
    height = (1-.16*q.move+.16*q.ready-.14*q.strike-.18*q.recover
              +.07*q.notice-.16*q.hurt)*(1-.88*d)
    direction = math.sin(q.yaw)/math.sin(YAW)
    bend = direction*(19*q.move-20*q.ready+10*q.strike-12*q.hurt)*u
    roll = (3.5+5*q.move)*math.sin(p-y*.043)*u*direction*(1-d)
    return (CX+(co*x+si*z)*width+bend+roll,
            GROUND+y*height,
            -si*x+co*z)


@dataclass(frozen=True)
class Billow:
    x: float
    y: float
    z: float
    rx: float
    ry: float
    density: float
    seed: float
    travel: float = 0.


# The cloud has three overlapping levels. The bottom level is broad and low.
# The middle level hides parts of the top level as the cloud turns.
# The x pairs have the same phase so the front view is continuous.
BILLOWS = (
    Billow(0,-109,-21,53,43,.86,0),
    Billow(-35,-124,-16,40,32,.82,1), Billow(35,-124,-16,40,32,.82,1),
    Billow(0,-136,-8,41,31,.83,2),
    Billow(-49,-91,-22,47,41,.88,3), Billow(49,-91,-22,47,41,.88,3),
    Billow(0,-95,7,56,50,.98,4),
    Billow(-48,-72,18,39,34,.92,5,.20), Billow(48,-72,18,39,34,.92,5,.20),
    Billow(-75,-40,-6,47,30,.88,6,.34), Billow(75,-40,-6,47,30,.88,6,.34),
    Billow(0,-44,27,60,35,.96,7,.70),
    Billow(-47,-30,39,51,27,.94,8,.80), Billow(47,-30,39,51,27,.94,8,.80),
    Billow(-90,-14,13,39,14,.70,9,.35), Billow(90,-14,13,39,14,.70,9,.35),
    Billow(0,-15,58,62,14,.92,10,.78),
)


def _billow(c, q, b, position, direction):
    """Draw one rounded gas volume with broad, curved density bands."""
    x,y,z = position
    p,d = q.cycle,q.death
    wave = math.sin(p+b.seed*1.9)
    width = (1+.13*q.move-.13*q.ready+.14*q.recover+.10*d)
    height = (1-.14*q.move+.13*q.ready-.12*q.strike-.17*q.recover)*(1-.88*d)
    rx = b.rx*width*(1+.08*wave+.20*q.strike*b.travel)
    ry = b.ry*height*(1+.08*math.cos(p+b.seed*1.3)+.24*q.strike*b.travel)
    # The lower and more distant gas is more transparent.
    fade = (1-d)**.82 * b.density
    if fade < .01:
        return
    facing = _clamp((z+65)/125.)
    low = _clamp((b.y+115)/95.)
    bright = _clamp(.20+.38*facing+.38*low+.20*q.strike*b.travel)
    mid = _mix(SHADOW, MID, .40+.60*bright)
    shadow = _mix(SHADOW, BASE, .46+.44*bright)
    light = _mix(BASE, LIGHT, .34+.66*bright)
    side = -1 if b.x < 0 else 1 if b.x > 0 else 0
    tilt = direction*(.09+.13*q.move+.15*q.strike*b.travel)
    swell = .10*math.sin(p+b.seed*2.1)
    # Composite each volume in a small local image. Overlapping volumes add
    # density instead of replacing each other's alpha values.
    margin = 4
    x0=math.floor(x-1.45*rx-margin)
    y0=math.floor(y-1.30*ry-margin)
    x1=math.ceil(x+1.45*rx+margin)
    y1=math.ceil(y+1.30*ry+margin)
    lobe=Canvas((x1-x0,y1-y0),super_scale=c.s)
    def T(u,v):
        return x-x0+rx*(u+tilt*v), y-y0+ry*v
    def C(u,v):
        return T((side or 1)*u,v)
    # A shared density color connects adjacent volumes. Only the internal
    # folds have shading, not a dark outline around every lobe.
    shape(lobe,C,(-1,.16),[((-1.08,-.36),(-.75,-.77),(-.46,-.76)),
          ((-.36,-1.06),(.18,-1.17),(.48,-.86)),
          ((.88,-.91),(1.13,-.40),(1.02,.13)),
          ((1.06,.60),(.50,.92),(.03,.86)),
          ((-.45,.95),(-.97,.64),(-1,.16))],_rgba(mid,fade*.96))
    if b.seed in (0,2,3,5,7,8):
        # The bright fold opens into the next cloud instead of closing around
        # its center. Its end changes as the cloud rolls.
        shape(lobe,C,(-.86,.10),[((-1.,-.39),(-.55,-.91),(-.10,-.89)),
              ((.25,-1.04),(.66,-.78),(.82,-.29)),
              ((.55,-.57),(.06,-.60),(-.24,-.40)),
              ((-.55,-.17),(-.50,.20+swell),(-.23,.43)),
              ((-.62,.36),(-.82,.29),(-.86,.10))],_rgba(light,fade*.94))
        if b.seed in (2,7):
            shape(lobe,C,(-.55,-.39),[((-.36,-.71),(-.02,-.85),(.30,-.73)),
                  ((.48,-.68),(.60,-.51),(.62,-.40)),
                  ((.24,-.62),(-.06,-.52),(-.30,-.33)),
                  ((-.44,-.23),(-.51,-.28),(-.55,-.39))],
                  _rgba(_mix(light,LIGHT,.65),fade*.80))
    else:
        # Smaller volumes have only a broad density crest.
        shape(lobe,C,(-.86,-.12),[((-.78,-.59),(-.34,-.89),(-.04,-.83)),
              ((.33,-.96),(.66,-.64),(.82,-.20)),
              ((.52,-.43),(.12,-.47),(-.22,-.30)),
              ((-.48,-.17),(-.70,.05),(-.86,-.12))],_rgba(light,fade*.86))
    if b.seed in (0,3,4,5,6,8,10):
        # Offset, open shadow regions describe the downward roll. No border.
        shape(lobe,C,(-.91,.29),[((-.65,.06),(-.40,.14),(-.17,.42)),
              ((.11,.10),(.64,.04),(.97,.34)),
              ((.76,.68),(.35,.89),(.04,.77)),
              ((-.36,.88),(-.71,.65),(-.91,.29))],_rgba(shadow,fade*.91))
    # Fade only a narrow edge. Keep the broad density folds sharp at game scale.
    image=lobe.image.filter(ImageFilter.GaussianBlur(.48*c.s))
    c.image.alpha_composite(image,(x0*c.s,y0*c.s))


def _positions(q):
    """Sort the volumes by depth in the current view."""
    p = q.cycle
    out = []
    for b in BILLOWS:
        sign = -1 if b.x < 0 else 1 if b.x > 0 else 0
        wave = math.sin(p+b.seed*1.9)
        x = b.x + sign*4*wave + sign*14*q.death
        y = b.y + 3.8*math.cos(p+b.seed*1.3)
        z = b.z + 5*wave
        # The forward gas expands and rolls away from the head during attack.
        z += b.travel*(68*q.strike-18*q.ready+18*q.recover)
        x *= 1+.08*q.strike*b.travel
        y -= 18*q.strike*b.travel
        out.append((_project(q,x,y,z),b))
    return sorted(out, key=lambda item: item[0][2])


def _wisp(c,q,x,y,z,rx,ry,alpha,phase_offset):
    """Draw a tapered, translucent ribbon of gas."""
    X,Y,_ = _project(q,x,y,z)
    direction = math.sin(q.yaw)/math.sin(YAW)
    # At the center of a turn the curl retains its volume.
    a = direction
    drift = math.sin(q.cycle+phase_offset)*.18
    def T(u,v):
        return X+rx*(u+(.25*a+drift)*v), Y+ry*v
    shape(c,T,(-1,.42),[((-.76,.03),(-.43,-.23),(-.09,-.13)),
          ((.34,.02),(.54,-.18),(.36,-.42)),
          ((.14,-.70),(.34,-1.06),(.86,-1.13)),
          ((.48,-.83),(.57,-.64),(.75,-.42)),
          ((1.08,-.06),(.73,.43),(.26,.35)),
          ((-.26,.24),(-.61,.28),(-1,.42))],_rgba(MID,alpha))
    shape(c,T,(-.72,.18),[((-.39,-.16),(-.12,-.18),(.14,-.09)),
          ((.53,.03),(.71,-.33),(.51,-.56)),
          ((.81,-.27),(.66,.16),(.26,.20)),
          ((-.07,.13),(-.39,.10),(-.72,.18))],_rgba(LIGHT,alpha*.61))


def _wisps(c,q,front):
    """Advect and fade the peripheral gas. It has no collision bounds."""
    p,d=q.cycle,q.death
    layer=Canvas(FRAME_SIZE,super_scale=c.s)
    for j in range(10):
        f=(p/math.tau+j/10)%1.
        life=math.sin(math.pi*f)**.85
        angle=math.tau*j/10+.32*math.sin(p+j)
        rad=62+41*f+19*d
        x=rad*math.sin(angle)
        z=rad*.68*math.cos(angle)+45*q.strike*f
        y=-13-23*(1-f)
        x0,y0,depth=_project(q,x,y,z)
        if (depth>=0)!=front: continue
        if life<.025: continue
        rx=(25+22*f)*life*(1+.16*q.strike)
        ry=(8+9*(1-f))*life*(1-.60*d)
        opacity=(.49 if front else .37)*life*(1-.84*d)
        _wisp(layer,q,x,y,z,rx,ry,opacity,j)
    # A few rising curls become faint well before they leave the dense cloud.
    if not front:
        for side in (-1,1):
            for j in range(2):
                f=(p/math.tau+j*.5+.17+(.24 if side>0 else 0.))%1.
                life=math.sin(math.pi*f)**.8
                x=side*(39+31*f)
                y=-116-47*f
                z=-18-15*f
                _wisp(layer,q,x,y,z,(32+20*f)*life,30*life,
                      .45*life*(1-d)**1.5,j+2.)
        for side in (-1,1):
            f=(p/math.tau+.27+(.5 if side>0 else 0.))%1.
            life=math.sin(math.pi*f)**.8
            _wisp(layer,q,side*(87+9*f),-43-15*f,-14,
                  (36+10*f)*life,21*life,.39*life*(1-d),side)
        for side in (-1,1):
            f=(p/math.tau+.32+(.43 if side>0 else 0.))%1.
            life=math.sin(math.pi*f)**.8
            _wisp(layer,q,side*(95+7*f),-15,0,
                  (42+12*f)*life,10*life,.43*life*(1-d),side+1.)
    c.image.alpha_composite(layer.image)


def _face(c,q):
    """Put the eyes in an irregular region of dense gas."""
    if q.death>=.72:
        return
    # The eyes are projected on a curved front surface. At no point is a
    # flattened portrait stretched into a new view.
    a=q.yaw
    head_y=-106-5*q.notice-4*q.ready
    # Use the same height and lean as the cloud, but the face leads the turn.
    def F(angle,y):
        theta=math.radians(angle)
        x,z=63*math.sin(theta),42*math.cos(theta)
        delta=a-q.mantle_yaw
        xx=x*math.cos(delta)+z*math.sin(delta)
        zz=-x*math.sin(delta)+z*math.cos(delta)
        return _project(q,xx,y,zz)[:2]
    # Layered, open density contours make the eye region part of the cloud.
    # The lower contour breaks into the cheek folds, instead of a mask rim.
    def D(u,v):return F(u,head_y+v)
    opacity=(1-q.death)**1.2
    shape(c,D,(-49,1),[((-54,-17),(-35,-27),(-15,-20)),
          ((-4,-17),(8,-20),(23,-22)),
          ((45,-24),(53,-9),(47,8)),
          ((40,20),(27,22),(19,29)),
          ((7,24),(1,16),(-10,21)),
          ((-32,27),(-45,19),(-49,1))],_rgba(SHADOW,.70*opacity))
    shape(c,D,(-40,-1),[((-39,-12),(-24,-17),(-10,-12)),
          ((-2,-9),(7,-11),(17,-15)),
          ((33,-19),(43,-10),(39,2)),
          ((33,13),(19,17),(9,15)),
          ((0,11),(-12,18),(-23,14)),
          ((-34,11),(-38,7),(-40,-1))],_rgba(DEEP,.90*opacity))
    # Blur only the density boundary. The eyes retain their crisp edges.
    c.image = c.image.filter(ImageFilter.GaussianBlur(2.5*c.s))
    c.d = ImageDraw.Draw(c.image)
    h=10.5*(1-.78*q.hurt)*(1-.25*q.ready)
    for side in (-1,1):
        ang=side*21.
        y=head_y-1+1.8*side*math.sin(a)
        # Both eyelids angle down toward the center, not toward one side.
        shape(c,F,(ang-15,y-4+side*4),[
            ((ang-8,y-5+side*4),(ang+6,y-3-side*4),(ang+15,y-side*4)),
            ((ang+8,y+h-side*2),(ang-6,y+h),(ang-15,y-4+side*4))],
            _rgba((241,246,186),opacity))
    if q.hurt>.40:
        x,y=F(0,head_y+19)
        c.oval((x,y),3.,4.,_rgba(DEEP,opacity),None)


def _paint(c,q):
    _wisps(c,q,False)
    # Rear and middle clouds overlap to create a continuous density field.
    direction=math.sin(q.yaw)/math.sin(YAW)
    volumes=_positions(q)
    body=Canvas(FRAME_SIZE,super_scale=c.s)
    for position,b in volumes:
        _billow(body,q,b,position,direction)
    # Soften the cloud edge without making the internal geometry blurry.
    halo=body.image.filter(ImageFilter.GaussianBlur(4.0*c.s))
    halo.putalpha(halo.getchannel('A').point(lambda a:round(a*.43)))
    c.image.alpha_composite(halo)
    c.image.alpha_composite(body.image)
    # The face sits in front of the upper mass. Low foreground gas does not
    # obscure its eyes, even at the peak of a surge.
    face=Canvas(FRAME_SIZE,super_scale=c.s)
    _face(face,q)
    c.image.alpha_composite(face.image)
    _wisps(c,q,True)
    # The last trace of a defeated elemental is a thin, low cloud.
    if q.death>.65:
        k=_clamp((q.death-.65)/.35)
        layer=Canvas(FRAME_SIZE,super_scale=c.s)
        for side in (-1,0,1):
            _wisp(layer,q,side*55,-16,8,42+8*abs(side),9,
                  .30*k,side*2.)
        c.image.alpha_composite(layer.image)


def _render_frame(anim,i,n):
    # Match the runtime's mirrored idle at the start of a turn. Interior
    # frames project the cloud at signed angles, including the front view.
    if anim=='turnaround' and i==0:
        return _render_frame('idle',0,24).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    c=Canvas(FRAME_SIZE,super_scale=2)
    _paint(c,pose(anim,i,n))
    return c.finish()


def _body_metrics(w,h):
    return body_metrics_for_box(BODY_BOX,w,h)


def render(out_dir: str | Path, **opts):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True,exist_ok=True)
    result = build_sheet(target=TARGET_NAME, rows=ROWS, render_fn=_render_frame,
                         out_dir=out_dir, frame_size=FRAME_SIZE, auto_crop=False,
                         actor_metadata=ACTOR_METADATA, body_metrics_fn=_body_metrics,
                         animation_key_map={a:a for a,_,_ in ROWS}, pose_bodies='authored')
    return [result[k] for k in ('spritesheet','yaml','ron','actor','preview',
                                'canonical','canonical_transparent')]
