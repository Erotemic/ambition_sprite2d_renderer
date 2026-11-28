"""The Element of Surprise: a living piece of folded comic-book art.

An asymmetric origami trickster unfolds into an expressive pop-up monster. Its
accordion folds and ribbon limbs change shape; they are not rigid bones.
The burst is art, not a new hitbox or an actual area-of-effect attack.
Muted ink at rest snaps into saturated print colors on the active strike.
The expanded silhouette lingers after the hit, then folds closed.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

from PIL import ImageEnhance

from . import _art_cast_kit as K
from ._clockwork_enemy_art import Canvas, mix, polar, rot, track, phase, bezier, add, sub, mul, unit, perp
from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'surprise_elemental'
FRAME_SIZE = (340, 270)
CX, CY = 141., 132.
WINDUP, ACTIVE, RECOVER = .38, .19, .76
TOTAL = WINDUP + ACTIVE + RECOVER
A, B = WINDUP / TOTAL, (WINDUP + ACTIVE) / TOTAL
# The visual reveal outlasts the damage window, without extending recovery.
REVEAL_HOLD_S = .30
HOLD_END = B + REVEAL_HOLD_S / TOTAL
ROWS = [('idle', 20, 65), ('walk', 20, 50), ('run', 20, 40),
        ('notice', 9, 50), ('windup', 13, 30), ('attack_side', 41, 33),
        ('hit', 9, 55), ('death', 21, 55)]
LOOPS = {'idle', 'walk', 'run'}
TRAITS = ['enemy', 'art', 'elemental', 'paper', 'surprise', 'floating']
ACTOR_METADATA = K.enemy_metadata(TARGET_NAME, 'Surprise Elemental', 'Floating',
    'Floating', 'Light', 'Fly', TRAITS,
    'A folded paper trickster which opens into a theatrical pop-up creature. A muted paper body snaps into loud printed colors during its theatrical reveal.')
ACTOR_METADATA['tags'] = TRAITS
ACTOR_METADATA['actions'] = {'default_preset': 'surprise_elemental_pop'}
ACTOR_METADATA['gameplay_description'] = 'Floats in a folded shape, draws its folds tight, then unfolds with a diving swipe. Confetti and graphic shock lines are visual only.'
ACTOR_METADATA['animation_bindings'].update({
    'locomotion.run': {'animation': 'run', 'events': []},
    'action.melee.primary': {'animation': 'attack_side', 'events': [
        {'t': A, 'event': 'hitbox_active_start', 'source': 'surprise_elemental.pop'},
        {'t': B, 'event': 'hitbox_active_end', 'source': 'surprise_elemental.pop'},
    ]},
})
INK = K.INK
VIOLET = K.VIOLET
PURPLE = K.VIOLET_DARK
CYAN = K.CYAN
CORAL = (255, 115, 129, 255)
WHITE = K.WHITE


@dataclass(frozen=True)
class Pose:
    cycle: float = 0.
    open: float = 0.
    coil: float = 0.
    strike: float = 0.
    move: float = 0.
    alarm: float = 0.
    hurt: float = 0.
    scatter: float = 0.
    death: float = 0.


def pose(anim, i, n):
    t = phase(i, n, anim in LOOPS)
    p = math.tau * (t % 1.)
    if anim == 'idle': return Pose(p)
    if anim in ('walk', 'run'): return Pose(p, move=.65 if anim == 'walk' else 1.)
    if anim == 'notice': return Pose(p, alarm=track(t, [(0,0),(.45,1),(1,.4)]))
    if anim == 'windup': return Pose(coil=track(t, [(0,0),(.8,1),(1,1)]), alarm=.12*t)
    if anim == 'attack_side':
        k = lambda keys: track(t, keys)
        return Pose(cycle=0.,
            open=k([(0,0),(A-.012,0),(A+.013,1),(HOLD_END,1),(1,0)]),
            coil=k([(0,0),(.8*A,1),(A-.012,1),(A+.013,0),(1,0)]),
            # Recoil from the hit while the paper fans and expression remain
            # open. The gameplay event boundaries A and B stay unchanged.
            strike=k([(0,0),(A-.012,0),(A+.013,1),(B,1),(B+.14,0),(1,0)]),
            alarm=k([(0,0),(A-.012,.12),(A+.013,1),(HOLD_END,1),(1,0)]),
            scatter=k([(0,0),(A,0),(A+.025,.12),(B,.4),(.92,1),(1,1)]))
    if anim == 'hit': return Pose(p, open=.32*math.sin(math.pi*t), hurt=math.sin(math.pi*t))
    if anim == 'death':
        d=track(t, [(0,0),(.18,.05),(.82,1),(1,1)])
        return Pose(open=track(t, [(0,0),(.25,1),(.63,.4),(1,0)]), death=d, scatter=d)
    raise ValueError(anim)


def _path(start, curves):
    """Sample authored cubic contours with the shared Bezier primitive."""
    points = [start]
    for b, c, end in curves:
        points.extend(bezier(points[-1], b, c, end, n=12)[1:])
    return points


def _fill(f, P, points, fill, edge=INK, width=2.):
    f.poly([P(*p) for p in points], fill, edge, width)


def _line(f, P, points, color, width=1.5):
    f.line([P(*p) for p in points], color, width)


# Material colors: saturated printed ink on ivory stock. The pale strips are
# paper edges, not emitted light. Keep the fold shadows in the same ink family.
TEAL = (23, 142, 169, 255)
NAVY = (36, 60, 119, 255)
BERRY = (157, 34, 105, 255)
ROSE = (244, 89, 155, 255)
SUN = (255, 200, 60, 255)
OCHRE = (189, 104, 45, 255)
IVORY = (255, 245, 219, 255)
IVORY_SHADOW = (217, 190, 185, 255)
LILAC = (166, 139, 187, 255)


def _fold(f, P, corners, light, dark, *, ridge=.42):
    """A folded paper flap with two planes and an exposed paper edge.

    Corners run from the base, via the outer tip and return edge, to the base.
    The ridge is attached to both planes; there are no detached decorative rays.
    """
    a, tip, b, root = corners
    crease = mix(a, b, ridge)
    _fill(f,P,[a,tip,b,root],light)
    _fill(f,P,[a,tip,crease,root],dark,None)
    _line(f,P,[tip,crease,root],INK,1.15)
    _line(f,P,[tip,b],K.shade(light,1.48),1.65)
    # A second folded-back sliver adds depth at the free tip. Keep it within
    # the existing face rather than adding disconnected decorative shapes.
    v=mix(tip,b,.26); w=mix(tip,crease,.21)
    _fill(f,P,[tip,v,w],K.shade(light,1.22),None)


def _opening_fold(f,P,o,closed,opened,light,dark,flutter=0.,coil=0.):
    corners=[mix(a,b,o) for a,b in zip(closed,opened)]
    root=corners[-1]
    # Draw in the fold during anticipation, and gently flex its free edge
    # during idle. The base stays attached to the paper body.
    a,tip,b,_=corners
    tip=add(mix(tip,root,.16*coil),(flutter,flutter*.65))
    b=add(mix(b,root,.08*coil),(flutter*.42,flutter*.25))
    _fold(f,P,[a,tip,b,root],light,dark)


def _ribbon(f,P,points,widths,light,dark):
    """A connected accordion strip; cross-sections follow the ribbon tangent."""
    edges=[]
    for j,(p,w) in enumerate(zip(points,widths)):
        tangent=sub(points[min(j+1,len(points)-1)],points[max(0,j-1)])
        normal=perp(unit(tangent))
        edges.append((add(p,mul(normal,-w)),add(p,mul(normal,w))))
    _fill(f,P,[a for a,b in edges]+[b for a,b in reversed(edges)],dark)
    for j,((a,b),(c,d)) in enumerate(zip(edges,edges[1:])):
        tone=light if j%2==0 else dark
        _fill(f,P,[a,c,d,b],tone,None)
        _line(f,P,[a,b],INK,1.4)
        _line(f,P,[a,c],K.shade(tone,1.45),1.1)
        if j%2==0:
            _fill(f,P,[mix(a,b,.65),mix(c,d,.65),d,b],K.shade(tone,.83),None)
    _line(f,P,[a for a,b in edges],INK,1.7)
    _line(f,P,[b for a,b in edges],INK,1.7)


def _hand(f,P,center,size,angle,far=False):
    def H(x,y):
        u,v=rot((x*size,y*size),angle)
        return P(center[0]+u,center[1]+v)
    # A three-fingered cut-paper hand, with a folded thumb and palm crease.
    outline=_path((-12,-10),[
        ((-5,-15),(3,-14),(9,-19)),
        ((15,-26),(19,-22),(17,-15)),
        ((17,-12),(10,-7),(11,-7)),
        ((22,-14),(31,-14),(30,-8)),
        ((29,-3),(20,-1),(16,0)),
        ((25,0),(34,3),(30,8)),
        ((28,13),(18,9),(13,8)),
        ((18,15),(20,20),(14,21)),
        ((8,21),(4,14),(-1,12)),
        ((-8,12),(-13,7),(-12,-10))])
    _fill(f,H,outline,IVORY_SHADOW if far else IVORY,INK,2.)
    _fill(f,H,[(-12,-10),(-2,-12),(4,-3),(-1,12),(-8,10),(-12,4)],LILAC if far else IVORY_SHADOW,None)
    _line(f,H,[(-2,-12),(4,-3),(-1,12)],LILAC,1.3)
    _line(f,H,[(4,-3),(11,-7)],LILAC,1.15)
    _line(f,H,[(4,-3),(13,8)],LILAC,1.15)
    _line(f,H,[(16,-16),(20,-20)],IVORY,1.2)


def _face(f,P,q):
    o,c=q.open,q.coil
    # One expressive mask, stretching as its folds release. No faceplate.
    sx=.88+.16*o-.08*c; sy=.86+.25*o-.07*c
    def H(x,y): return P(5+x*sx,-8+y*sy-9*o+3*c)
    contour=_path((-31,-24),[
        ((-26,-39),(-9,-46),(9,-39)),
        ((24,-38),(36,-27),(37,-11)),
        ((43,1),(39,16),(26,26)),
        ((15,39),(-1,42),(-16,33)),
        ((-34,24),(-44,10),(-39,-7)),
        ((-37,-14),(-35,-19),(-31,-24))])
    _fill(f,H,contour,IVORY,INK,2.6)
    # Shadow on the turned-back plane, following the silhouette.
    shade=_path((-31,-24),[
        ((-37,-12),(-44,1),(-38,14)),
        ((-32,28),(-24,34),(-16,33)),
        ((-17,23),(-23,15),(-23,5)),
        ((-27,-7),(-24,-19),(-19,-26)),
        ((-21,-33),(-26,-32),(-31,-24))])
    _fill(f,H,shade,IVORY_SHADOW,None)
    _line(f,H,[(-29,-26),(-17,-32),(3,-34)],WHITE,1.7)
    wide=max(o,.52*q.alarm,.30*q.hurt)
    blink=1.0
    if q.cycle:
        blink=1.-.93*max(0.,1.-abs((q.cycle/math.tau)-.76)/.065)
    # Far eye is smaller. The eyes use a continuous lid opening and separate
    # irises, so the surprise is readable even before the large silhouette.
    for ex,ey,rx in [(-9,-9,9.1),(19,-9,10.2)]:
        ry=(3.7+10.7*wide)*max(.12,blink)*(1-.22*c)
        pts=[(ex+rx*math.cos(t),ey+ry*math.sin(t)) for t in (math.tau*j/36 for j in range(36))]
        _fill(f,H,pts,WHITE,INK,1.9)
        if ry>1.3:
            pupil=rx*(.58-.18*wide)
            pr=ry*(.84-.12*wide)
            _fill(f,H,[(ex+2.1+pupil*math.cos(t),ey+pr*math.sin(t)) for t in (math.tau*j/28 for j in range(28))],INK,None)
            _fill(f,H,[(ex+2.1+1.3*math.cos(t),ey-pr*.38+1.35*math.sin(t)) for t in (math.tau*j/16 for j in range(16))],WHITE,None)
        brow=_path((ex-rx-1,ey-ry-3-6*wide),[((ex-5,ey-ry-6-9*wide),(ex+3,ey-ry-5-7*wide),(ex+rx,ey-ry-3-2*wide))])
        _line(f,H,brow,INK,3.1)
    # Tiny folded nose and two print-colored cheek accents.
    _fill(f,H,[(7,-4),(12,8),(4,7)],IVORY_SHADOW,None)
    _line(f,H,[(7,-4),(12,8),(7,7)],LILAC,1.0)
    for ex in (-22,29):
        _fill(f,H,[(ex-3,8),(ex+3,9),(ex+2,12),(ex-4,11)],(239,158,160,255),None)
    # A closed, slightly smug smile expands into a comic O-shaped shout.
    if wide<.10:
        _line(f,H,_path((-2,15),[((6,21),(17,20),(24,13))]),INK,2.3)
        _line(f,H,[(21,12),(25,14)],INK,1.4)
    else:
        x,y=10.,19.
        rx=5+10*wide; ry=2+13*wide
        mouth=_path((x-rx,y-1),[
            ((x-rx,y-ry),(x+rx*.68,y-ry*1.15),(x+rx,y-2)),
            ((x+rx*1.05,y+ry*.62),(x+rx*.4,y+ry),(x-1,y+ry)),
            ((x-rx*.78,y+ry*.93),(x-rx,y+ry*.3),(x-rx,y-1))])
        _fill(f,H,mouth,INK,None)
        if wide>.32:
            _fill(f,H,[(x-rx*.71,y-ry*.59),(x+rx*.65,y-ry*.62),(x+rx*.61,y-ry*.22),(x-rx*.65,y-ry*.22)],WHITE,None)
            _fill(f,H,_path((x-rx*.51,y+ry*.70),[((x-rx*.30,y+ry*.27),(x+rx*.35,y+ry*.22),(x+rx*.53,y+ry*.69)),((x+rx*.15,y+ry*.91),(x-rx*.24,y+ry*.91),(x-rx*.51,y+ry*.70))]),CORAL,None)


# Keep the color envelope separate from the geometry and hit timing. Printed
# paper becomes slightly duller as the creature compresses, then the same
# authored colors snap into full chroma with the unfolding. Hold the color
# through the strike and the held reveal, then let it drain as the folds close.
REST_SATURATION = .13
FULL_SATURATION = 1.10


def _ink_saturation(anim, q):
    muted = REST_SATURATION - .065*q.coil
    if anim == 'attack_side':
        reveal = max(q.open, q.strike)
        return muted + (FULL_SATURATION - muted)*reveal
    if anim == 'death':
        return REST_SATURATION*(1-q.death)
    return muted


def _render_frame(anim,i,n):
    q=pose(anim,i,n); f=Canvas(FRAME_SIZE)
    o,c,h,d=q.open,q.coil,q.strike,q.death
    flow=math.sin(q.cycle); flow2=math.cos(q.cycle)
    cx=CX+5*q.move+10*h-7*c-7*q.hurt
    cy=CY+3.5*flow+5*c-7*h+24*d
    tilt=7*q.move+3.5*flow-10*c+7*h-15*q.hurt
    def P(x,y):
        u,v=rot((x*(1+.09*c),y*(1-.13*c)),tilt)
        return (cx+u,cy+v)

    # Trailing folded ribbon: a tapering S made of two broad printed planes.
    tx=-9-13*o-10*q.move+4*flow
    tail=_path((-27,26),[
        ((-50,51),(-20,70),(tx-13,74)),
        ((tx+6,80),(tx-18,92),(tx-25,98)),
        ((tx+7,95),(tx+19,79),(tx+4,65)),
        ((-5,48),(10,42),(7,26))])
    _fill(f,P,tail,NAVY)
    _fill(f,P,_path((-27,26),[((-50,51),(-20,70),(tx-13,74)),((tx+6,80),(tx-18,92),(tx-25,98)),((tx-7,87),(tx+4,76),(tx-3,66)),((-32,55),(-20,45),(-8,32))]),CYAN,None)
    _line(f,P,_path((-22,36),[((-37,54),(-14,64),(tx+1,70)),((tx+8,80),(tx-6,88),(tx-18,93))]),K.shade(CYAN,1.55),1.6)

    # Far arm unfurls from a folded side panel, behind the paper mantle.
    far_closed=[(-20,5),(-37,8),(-43,20),(-35,27),(-38,31)]
    far_open=[(-25,8),(-44,-10),(-55,-1),(-70,-21),(-78,-32)]
    far=[mix(a,b,o) for a,b in zip(far_closed,far_open)]
    _ribbon(f,P,far,[10,8,10,8,7],TEAL,NAVY)
    _hand(f,P,far[-1],.22+.60*o,150+28*o,True)

    # Main folded stock, not a radial star. The broad faces form an origami
    # mantle that opens into five individually hinged paper fans.
    body=[(-47,-15),(-34,-45),(-12,-54),(22,-44),(43,-23),(44,12),(28,40),(-8,57),(-36,39),(-52,9)]
    expanded=[(-53,-11),(-42,-42),(-16,-49),(29,-39),(49,-17),(48,17),(30,45),(-6,61),(-42,40),(-61,8)]
    shell=[mix(a,b,o) for a,b in zip(body,expanded)]
    _fill(f,P,shell,NAVY,INK,2.8)
    _fill(f,P,[shell[0],shell[1],shell[2],(0,-8),(-17,24),shell[-2],shell[-1]],TEAL,None)
    _fill(f,P,[shell[2],shell[3],shell[4],(23,8),(1,18),(0,-8)],VIOLET,None)
    _fill(f,P,[shell[-2],(-17,24),(1,18),(23,8),shell[5],shell[6],shell[7]],BERRY,None)
    _line(f,P,[shell[1],shell[2],(0,-8)],K.shade(TEAL,1.55),2.)

    # Large, asymmetric paper fan with a recurved crest; each flap hinges
    # from its resting shape into a single, connected open silhouette.
    folds=[
        ([(-42,-20),(-44,-46),(-9,-35),(-16,8)], [(-42,-17),(-86,-59),(-39,-54),(-15,10)], CYAN,NAVY),
        ([(-32,-32),(-18,-68),(8,-41),(-2,-10)], [(-32,-28),(-51,-100),(11,-56),(1,-7)], VIOLET,PURPLE),
        ([(-4,-40),(20,-58),(36,-30),(10,-12)], [(-6,-42),(17,-100),(47,-52),(13,-10)], SUN,OCHRE),
        ([(20,-31),(46,-31),(49,-1),(21,7)], [(27,-35),(76,-65),(61,-17),(22,9)], ROSE,BERRY),
        ([(-44,4),(-56,24),(-25,37),(-16,17)], [(-46,3),(-89,19),(-48,52),(-12,23)], ROSE,BERRY),
        ([(-27,28),(-30,53),(5,56),(4,28)], [(-30,28),(-51,77),(9,64),(7,26)], SUN,OCHRE),
    ]
    for j,(closed,opened,light,dark) in enumerate(folds):
        flutter=1.4*math.sin(q.cycle+j*.93)*(1-o)
        _opening_fold(f,P,o,closed,opened,light,dark,flutter,c)
    # Front fold below the mask is a single cream-paper edge and blue reverse.
    _fill(f,P,[(-42,15),(-18,35),(8,43),(30,25),(21,49),(-8,58),(-35,39)],TEAL)
    _fill(f,P,[(-42,15),(-18,35),(8,43),(-8,52),(-35,39)],CYAN,None)
    _line(f,P,[(-42,15),(-18,35),(8,43),(30,25)],IVORY,1.8)

    # Near arm opens outward as the face opens, from the bottom of the mask
    # so it never covers the eyes. A full-width paper strip visibly unfolds.
    near_closed=[(24,22),(39,25),(43,33),(38,40),(31,45)]
    # The hand retracts into a lower open-arm pose during the held reveal;
    # full extension is reserved for the strike, not the lingering display.
    if anim == 'attack_side':
        near_open=[(25,23),(46+5*h,39-5*h),(53+12*h,33-18*h),
                   (71+12*h,39-11*h),(88+29*h,32-13*h)]
    else:
        near_open=[(25,23),(51,34),(65,15),(83,28),(105+12*h,13+6*h)]
    near=[mix(a,b,o) for a,b in zip(near_closed,near_open)]
    _ribbon(f,P,near,[11,10,11,10,8],ROSE,BERRY)
    _hand(f,P,near[-1],.28+.72*o,-20-9*h)
    _face(f,P,q)

    # A handful of paper chips with motion tied to the unfolding. These are
    # visual accents, not collision geometry. Use a short, strong ink swoosh.
    if 0<q.scatter<1:
        u=q.scatter; life=math.sin(math.pi*u)**.7
        for j,(a,r,col) in enumerate([(-144,98,CYAN),(-109,116,SUN),(-66,111,ROSE),(-32,120,SUN),(15,125,CYAN),(59,105,ROSE),(128,100,SUN)]):
            x,y=polar(54+(r-54)*u,a); y+=22*u*u
            size=(4.0+2.0*(j%3))*life
            pts=[add((x,y),rot(v,a+130*u)) for v in [(-size,-size*.42),(size*.8,-size*.42),(size,size*.42),(-size*.65,size*.65)]]
            _fill(f,P,pts,col,INK,.8)
        if h>.18:
            # Accent the moving hand without placing rays ahead of the hitbox.
            # The parallel tapered strokes follow the direction of extension.
            for j,(dx,dy) in enumerate(((0,-26),(8,-33),(-4,28))):
                x=near[-1][0]+dx; y=near[-1][1]+dy
                extent=(12+5*(j%2))*h
                _fill(f,P,[(x-extent,y+2),(x+3,y-1),(x-extent*.36,y-3)],IVORY if j==0 else SUN,None)
    im=f.finish()
    # Pillow's luminance-based color adjustment keeps the paper's printed
    # value structure and preserves alpha; no alternate geometry or palette
    # maintenance is needed for the two states.
    alpha=im.getchannel('A')
    im=ImageEnhance.Color(im).enhance(_ink_saturation(anim,q))
    im.putalpha(alpha)
    if d>0:
        im.putalpha(im.getchannel('A').point(lambda a: round(a*(1-d))))
    return im


def _body_metrics(w,h):
    return body_metrics_for_box((96,86,186,199),w,h)


def render(out_dir: str | Path, **opts):
    outputs=build_sheet(target=TARGET_NAME,rows=ROWS,render_fn=_render_frame,
        out_dir=Path(out_dir),frame_size=FRAME_SIZE,auto_crop=False,
        actor_metadata=ACTOR_METADATA,body_metrics_fn=_body_metrics,
        animation_key_map={name:name for name,_,_ in ROWS})
    return [outputs[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]
