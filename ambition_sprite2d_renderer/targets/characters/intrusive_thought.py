"""The Intrusive Thought in the Neural Cathedral.

A cloud of purple ink holds three fragments of speech. The fragments press
against its face before it charges. They scatter when it takes a hit.
"""
from __future__ import annotations

import math
from pathlib import Path

from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box
from . import _art_cast_kit as K

TARGET_NAME = "intrusive_thought"
FRAME_SIZE = (176, 148)
ROWS = [
    ("idle", 12, 90), ("walk", 12, 70), ("notice", 8, 70), ("windup", 8, 65),
    ("attack_side", 25, 50), ("hit", 7, 60), ("death", 14, 70),
]
# The purple core sets the scale. The speech fragments can move away from it.
BODY_BOX = (49, 39, 119, 103)
WINDUP_S, ACTIVE_S, RECOVERY_S = .45, .20, .60
TOTAL_S = WINDUP_S + ACTIVE_S + RECOVERY_S

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Intrusive Thought", "Blob", "Small", "Light", "Float", ["thought", "floating", "cloud"],
    "A cloud of purple ink with amber eyes and a mouth that widens as it charges. Fragments of speech repeat around "
    "it. They bunch up before the charge and peel away when it is hit.",
)
ACTOR_METADATA["tags"] = ["enemy", "neural", "thought"]

INK = (34, 17, 54, 255)
VELVET = (57, 28, 85, 255)
PURPLE = (111, 52, 145, 255)
ORCHID = (177, 91, 186, 255)
LIGHT = (224, 145, 214, 255)
GOLD = (255, 221, 135, 255)
PAPER = (241, 220, 242, 255)


def _smooth(t):
    t = min(1.0, max(0.0, t))
    return t*t*(3-2*t)


def _curve(points):
    """Sample the cubic segments of a closed shape or an interior stroke."""
    result = [points[0]]
    for i in range(0, len(points)-1, 3):
        a, b, c, d = points[i:i+4]
        for j in range(1, 9):
            t = j/8
            u = 1-t
            result.append(tuple(u**3*a[k]+3*u*u*t*b[k]+3*u*t*t*c[k]+t**3*d[k] for k in range(2)))
    return result


def _speech(f, centre, mouth, scale, kind, opacity):
    x, y = centre
    rx, ry = ((12.0, 8.0), (10.0, 10.5), (9.0, 7.0))[kind]
    rx, ry = rx*scale, ry*scale
    dx, dy = mouth[0]-x, mouth[1]-y
    distance = max(1, math.hypot(dx, dy))
    ux, uy = dx/distance, dy/distance
    ex, ey = x+rx*ux*.76, y+ry*uy*.76
    tail = [(ex-3*uy*scale,ey+3*ux*scale), (ex+3*uy*scale,ey-3*ux*scale),
            (ex+6*ux*scale,ey+6*uy*scale)]
    f.ellipse(x, y, rx+1.35, ry+1.35, K.alpha(INK,opacity), body=False)
    f.poly(tail, K.alpha(INK,opacity), body=False)
    f.ellipse(x, y, rx, ry, K.alpha(PAPER,opacity), body=False)
    f.poly([(ex-2.1*uy*scale,ey+2.1*ux*scale), (ex+2.1*uy*scale,ey-2.1*ux*scale),
            (ex+4.2*ux*scale,ey+4.2*uy*scale)], K.alpha(PAPER,opacity), body=False)

    def line(points):
        f.ink([(x+px*scale,y+py*scale) for px,py in points],1.9*scale,K.alpha(VELVET,opacity))

    if kind == 0:
        for dot in (-4, 0, 4):
            f.ellipse(x+dot*scale,y,1.2*scale,1.2*scale,K.alpha(VELVET,opacity),body=False)
    elif kind == 1:
        line([(-3,-3),(-2,-5),(2,-5),(3,-3),(2,-1),(0,1),(0,2)])
        f.ellipse(x,y+4.6*scale,1.0*scale,1.0*scale,K.alpha(VELVET,opacity),body=False)
    else:
        line([(-4,-1),(-1,2),(1,-1),(4,1)])


def _cloud(f, point, breath, gaze, opening, flinch):
    def face(points):
        return [point(x,y) for x,y in points]

    def fill(points, colour, body=False):
        f.poly(face(_curve(points)), colour, body=body)

    fill([(-44,10),(-43,1),(-42,-9),(-30,-17), (-28,-34),(-7,-39),(1,-27),
          (13,-40),(33,-35),(36,-21), (46,-21),(51,-12),(44,-3),
          (56,9),(45,23),(29,25), (23,36),(10,35),(3,28),
          (-9,37),(-24,30),(-28,22), (-37,28),(-48,24),(-51,18),
          (-45,19),(-42,15),(-44,10)], PURPLE, True)
    fill([(-47,19),(-36,19),(-31,11),(-24,10),(-12,19),(7,18),(16,10),
          (33,9),(44,11),(46,15),(40,22),(34,25),(29,25),
          (22,32),(13,33),(3,28),(-8,34),(-23,31),(-28,22),(-38,28),(-46,24),(-47,19)], VELVET)
    fill([(-36,-5),(-34,-10),(-28,-15),(-25,-16),(-25,-29),(-10,-34),(-3,-28),
          (-9,-28),(-13,-23),(-11,-18),(-19,-21),(-23,-16),(-22,-12),(-29,-14),(-33,-9),(-36,-5)], ORCHID)
    fill([(1,-23),(11,-35),(28,-33),(32,-24),(26,-29),(17,-25),(15,-20),
          (10,-23),(6,-23),(1,-23)], ORCHID)
    for points, colour, w in [
        ([(-31,2),(-23,-6),(-27,-12),(-18,-14)], ORCHID,2.0),
        ([(2,-29),(-4,-25),(-5,-21),(-3,-18)], LIGHT,1.6),
        ([(34,-20),(37,-13),(35,-10),(30,-8)], ORCHID,1.7),
        ([(-18,22),(-12,26),(-3,26),(0,23)], ORCHID,1.6),
    ]:
        f.ink(face(_curve(points)),w,colour)

    for x, y, width in [(-7,-6,8), (15,-5,11)]:
        height = (6.4+breath*1.5)*(1-.93*flinch)
        brow = -3 if x>0 else 1.8
        eye = [(x-width,y+brow*.65),(x-width*.3,y-height+brow),(x+width*.55,y-height-brow),(x+width,y-brow*.65),
               (x+width*.42,y+height),(x-width*.56,y+height),(x-width,y+brow*.65)]
        fill(eye, INK)
        if flinch < .85:
            fill([(x-width+1.5,y+brow*.65+.7),(x-width*.2,y-height+brow+1.3),
                  (x+width*.50,y-height-brow+1.4),(x+width-1.5,y-brow*.65+.7),
                  (x+width*.35,y+height*.75),(x-width*.48,y+height*.72),(x-width+1.5,y+brow*.65+.7)], GOLD)
            xp, yp = point(x+gaze,y+.7)
            f.ellipse(xp,yp,1.95,2.7,INK,body=False)
            f.ellipse(xp-.75,yp-.9,.6,.6,PAPER,body=False)
        else:
            f.ink(face([(x-width+1,y),(x+width-1,y-1)]),1.4,GOLD)

    lower = 17+19*opening
    lip = 31+6*opening
    fill([(-9,11),(-4,5),(14,9),(lip,7), (lip+1,lower),(13,lower+5),(-9,11)], INK)
    fill([(-2,12),(7,12),(21,10),(lip-3,9),(lip-7,14),(6,16),(-2,12)], LIGHT)
    if opening > .2:
        f.ink(face(_curve([(3,lower-8),(15,lower-4),(28,lower-10),(lip-3,lower-15)])),2.1,ORCHID)


def _render_frame(anim, i, n):
    t = K.phase(i,n,anim in K.LOOPS)
    wave = math.tau*t
    x, y = 87.0, 71.0 + 2.7*math.sin(wave)
    sx, sy = 1.0, 1.0
    orbit, spread = wave, 1.0
    breath, gaze, opening, flinch, strike = 0.0, 2.6, .06, 0.0, 0.0
    disperse = 0.0
    if anim == "walk":
        x += 4
        sx, sy = 1.07, .91
        orbit = wave + .60
    elif anim == "notice":
        y -= 3.5
        breath, gaze, opening = .78, 3.4, .31
        sy = 1.07
    elif anim == "windup":
        x -= 5.0
        sx, sy = .98, 1.18+.025*math.sin(wave)
        breath, gaze, opening = .96, 4.0, .46
        orbit, spread = wave*2, .84
    elif anim == "attack_side":
        time = t*TOTAL_S
        end = WINDUP_S + ACTIVE_S
        strike = _smooth((time-WINDUP_S)/.09)*(1-_smooth((time-end)/.24))
        coil = _smooth(time/WINDUP_S)*(1-_smooth((time-.73)/.44))
        x += 13*strike - 5*coil
        sx, sy = 1.0+.13*strike, 1.0+.17*coil-.22*strike
        breath, gaze, opening = coil, 2.6+1.8*coil, .06+.39*coil+.55*strike
        spread = 1.0-.16*coil+.25*strike
    elif anim == "hit":
        flinch = math.sin(math.pi*t)
        x -= 9*flinch
        sx, sy, spread = 1-.16*flinch, 1-.14*flinch, 1+.26*flinch
        opening = .32*flinch
    elif anim == "death":
        disperse = _smooth(t)
        flinch, spread = 1.0, 1+.24*disperse
        sx, sy = 1-.65*disperse, 1-.65*disperse

    def point(dx,dy):
        return (x+dx*sx,y+dy*sy)

    f = K.Frame(FRAME_SIZE)
    if strike > .04:
        for dx, dy in [(-31,-12),(-26,15),(-18,27)]:
            f.poly([point(dx-25*strike,dy+1),point(dx,dy-2),point(dx-4,dy+3)],K.alpha(LIGHT,.72*strike), body=False)
    for k in range(3):
        a = orbit + math.tau*k/3
        reach_x = (47-8*strike)*spread
        bx = min(160,max(16,x-8*strike+math.cos(a)*reach_x))
        by = y+math.sin(a)*38*spread-5
        scale = .81+.14*math.cos(a)
        _speech(f,(bx,by),point(16,11),scale,k,1-_smooth((disperse-.38)/.62))
    f.glow(*point(0,0),33,K.alpha(ORCHID,.20*(1-disperse)))
    if disperse < .98:
        _cloud(f, point, breath, gaze, opening, flinch)
    if strike > .08:
        for dx, dy in [(41,12),(47,14)]:
            f.ink([point(dx,dy-6),point(dx+3,dy-2),point(dx+3,dy+2),point(dx,dy+5)],
                  1.5,K.alpha(PAPER,.56*strike))
    if disperse > .1:
        for k in range(6):
            a = k*math.tau/6
            cx, cy = x+math.cos(a)*disperse*51,y+math.sin(a)*disperse*40
            r = 4+3*math.sin(a+1.5)
            f.ellipse(cx,cy,r,r*.63,K.alpha(ORCHID,.85*(1-disperse)),body=False)
    return f.finish(outline=INK, width=1.7, glow_blur=3.1, fade=(1-disperse)**.75)


def render(out_dir: str | Path, **opts):
    outputs = build_sheet(target=TARGET_NAME, rows=ROWS, render_fn=_render_frame, out_dir=Path(out_dir),
                          frame_size=opts.get("frame_size", FRAME_SIZE), auto_crop=False, actor_metadata=ACTOR_METADATA,
                          body_metrics_fn=lambda width,height: body_metrics_for_box(BODY_BOX,width,height),
                          pose_bodies="authored", animation_key_map={name:name for name,_,_ in ROWS})
    return [outputs[key] for key in ("spritesheet", "yaml", "ron", "actor", "preview", "canonical", "canonical_transparent")]


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
