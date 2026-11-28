"""A mature, broad-shouldered imp; a mid-game airborne ranged skirmisher.

The silhouette is authored independently from the small imp. The wing ribs,
membranes and claws share joint positions; the two arms have explicit depth
layers and distinct poses. No projectile is baked into the sprite.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from ._magic_character_art import Canvas, add, bezier, phase, rot, track
from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'greater_imp'
FRAME_SIZE = (344, 306)
ORIGIN = (172, 153)
# Body, not the extremities of wings, tail or horns.
BODY_BOX = (140, 86, 216, 234)
ROWS = [
    ('idle', 16, 64), ('walk', 16, 56), ('run', 16, 45), ('fly', 16, 48),
    ('notice', 10, 42), ('aim', 18, 42), ('windup', 18, 42),
    ('shoot', 9, 40), ('hit', 10, 48), ('death', 22, 55),
]
TRAITS = ['enemy', 'fantasy', 'monster', 'imp', 'winged']
ACTOR_METADATA = {
    'actor': {'character_id': TARGET_NAME, 'display_name': 'Greater Imp'},
    'body': {'body_plan': 'Biped', 'body_kind': 'Floating',
             'mass_class': 'Medium', 'locomotion_hint': 'Fly', 'traits': TRAITS},
    'brain': {'default_preset': 'skirmisher_ranger'},
    'actions': {'default_preset': 'greater_imp_flame'},
    'visual': {'default_pose': 'idle', 'portrait': {'animation': 'idle', 'frame': 0}},
    'tags': TRAITS,
    'authoring_description': (
        'A mature charcoal-slate imp with a muscular chest, long hooked claws, '
        'backward-swept ridged horns, a narrow predatory face and broad ribbed wings.'),
    'gameplay_description': (
        'A larger airborne skirmisher. It braces, ignites its throat and spits '
        'a short volley of heavy firebolts along a committed firing lane.'),
    'animation_bindings': {
        'default': {'animation': 'idle', 'events': []},
        'locomotion.walk': {'animation': 'walk', 'events': []},
        'locomotion.run': {'animation': 'run', 'events': []},
        'locomotion.fly': {'animation': 'fly', 'events': []},
        'action.ranged.primary': {'animation': 'shoot', 'events': [
            {'t': 0.0, 'event': 'projectile_release', 'source': 'greater_imp.flame'}]},
        'combat.hurt': {'animation': 'hit', 'events': []},
        'combat.death': {'animation': 'death', 'events': []},
    },
}

INK = '#1e1924'
SKIN = '#514c5c'
SHADE = '#363140'
FAR = '#3e3949'
LIGHT = '#77717e'
RIDGE = '#91858a'
HORN = '#b6a18a'
HORN_DARK = '#796b67'
WING = '#443446'
WING_LIGHT = '#695365'
WING_DARK = '#312638'
CLAW = '#bead99'
EYE = '#f3cb61'
EMBER = '#e97a32'
HOT = '#ffd48b'


@dataclass(frozen=True)
class Pose:
    p: float
    bob: float = 0.
    pitch: float = 0.
    charge: float = 0.
    shoot: float = 0.
    alert: float = 0.
    hurt: float = 0.
    death: float = 0.


def _pose(anim, i, n):
    t = phase(i, n, anim in ('idle', 'walk', 'run', 'fly'))
    p = math.tau * t
    if anim == 'idle':
        return Pose(p, 2.5 * math.sin(p))
    if anim in ('walk', 'run', 'fly'):
        return Pose(p, 3 * math.sin(p), 16 if anim == 'run' else 10)
    if anim == 'notice':
        a = track(t, [(0, 0), (.45, 1), (1, .62)])
        return Pose(p, -5*a, -9*a, alert=a)
    if anim in ('aim', 'windup'):
        a = track(t, [(0, 0), (.72, .85), (1, 1)])
        return Pose(p, -3*a, -11*a, charge=a)
    if anim == 'shoot':
        a = track(t, [(0, 1), (.20, .85), (.6, .22), (1, 0)])
        return Pose(p, 3*a, -15*a, charge=.35*a, shoot=a)
    if anim == 'hit':
        a = math.sin(math.pi*t)
        return Pose(p, 3*a, -24*a, hurt=a)
    if anim == 'death':
        a = track(t, [(0, 0), (.12, .25), (.38, .7), (1, 1)])
        return Pose(p, 14*a, -49*a, hurt=min(1., 1.3*a), death=a)
    raise ValueError(anim)


def _render_frame(anim: str, i: int, n: int):
    q = _pose(anim, i, n)
    c = Canvas(FRAME_SIZE)
    p = q.p
    origin = (ORIGIN[0], ORIGIN[1]+q.bob)
    death = q.death
    recoil = max(q.hurt, death)

    def P(x, y):
        return add(origin, rot((x, y), q.pitch))

    def poly(pts, fill, edge=INK, width=2.1):
        c.poly([P(*v) for v in pts], fill, edge, width)

    def line(pts, fill=INK, width=1.8):
        c.line([P(*v) for v in pts], fill, width)

    def oval(x, y, rx, ry, fill, edge=INK, width=1.8, angle=0):
        c.oval(P(x, y), rx, ry, fill, edge, width, angle+q.pitch)

    def path(start, *segments):
        pts = [start]
        for a, b, end in segments:
            pts.extend(bezier(pts[-1], a, b, end, 16)[1:])
        return pts

    def shape(start, *segments, fill, edge=INK, width=2.1):
        poly(path(start, *segments), fill, edge, width)

    def limb(joints, widths, fill, light):
        # The contour uses shared normals at joints; no detached joint discs
        # or mechanical line caps are visible between the upper/lower limb.
        norms = []
        for j, a in enumerate(joints):
            b = joints[max(0,j-1)]
            d = joints[min(len(joints)-1,j+1)]
            vx, vy = d[0]-b[0], d[1]-b[1]
            l = max(.001, math.hypot(vx,vy))
            norms.append((-vy/l,vx/l))
        left = [(a[0]+w*v[0],a[1]+w*v[1]) for a,w,v in zip(joints,widths,norms)]
        right = [(a[0]-w*v[0],a[1]-w*v[1]) for a,w,v in zip(joints,widths,norms)]
        # Round the outline vertices for the fleshy arms and legs. The
        # densely sampled tail already has smooth curvature.
        contour = left+right[::-1]
        if len(joints) <= 6:
            rounded = []
            for k, v in enumerate(contour):
                a, b = contour[k-1], contour[(k+1)%len(contour)]
                start = (v[0]*.76+a[0]*.24, v[1]*.76+a[1]*.24)
                end = (v[0]*.76+b[0]*.24, v[1]*.76+b[1]*.24)
                rounded.extend(bezier(start,v,v,end,6))
            contour = rounded
        poly(contour,fill)
        if light:
            line([(a[0]+w*.5*v[0],a[1]+w*.5*v[1]) for a,w,v in zip(joints,widths,norms)], light, 2)

    # Tail: thick root, tapered flexible length, hooked bony tip. The tip
    # follows the tangent, not a fixed world-oriented arrowhead.
    wag = 8*math.sin(p-.7)
    tail_tip = (-105-3*death, 16+wag+21*death)
    tail = path((-17, 26), ((-43,52),(-89,61),(-108,42+wag)),
                ((-124,28+wag),(-114,15+wag+18*death),tail_tip))
    widths = [8.8*(1-k/(len(tail)-1))**.75+2.2 for k in range(len(tail))]
    limb(tail,widths,SKIN,RIDGE)
    dx,dy=tail[-1][0]-tail[-3][0],tail[-1][1]-tail[-3][1]
    angle=math.degrees(math.atan2(dy,dx))
    def T(x,y): return add(tail_tip,rot((x,y),angle))
    shape(T(-6,-4),(T(1,-9),T(14,-11),T(20,-2)),
          (T(11,-1),T(9,9),T(2,6)),(T(-3,4),T(-5,3),T(-6,-4)),fill=HORN_DARK)
    line([T(0,-4),T(11,-5),T(17,-2)],HORN,1.5)

    # Wings always sit behind both arms and the head. Each membrane shares
    # the exact same wrist and finger endpoints as its drawn spars.
    def wing(far):
        beat=math.sin(p+(.42 if far else 0))
        fold=min(.64,.47*death+.15*q.hurt+.10*q.charge)
        hinge=(12,-28) if far else (-16,-26)
        span=(.84+.12*math.cos(p+(.42 if far else 0)))*(1-fold)
        depth=.79 if far else 1.
        side=-1 if far else 1
        tilt=side*(13*beat-11*q.charge+66*death- (12 if far else 0))
        def W(x,y):
            return add(hinge,rot((side*x*span*depth,y*(1-.45*death)),tilt))
        sh=W(0,0)
        wrist=W(-63,-54-15*beat)
        thumb=W(-59,-70-15*beat)
        tips=[W(-136,-57-10*beat),W(-124,-3+12*beat),W(-94,43+15*beat),W(-55,47+10*beat),W(-8,19)]
        outline=[sh,wrist,thumb,W(-69,-61-15*beat),tips[0]]
        # Concave scallops between individual wing fingers.
        for a,b in zip(tips,tips[1:]):
            ca=(a[0]*.72+wrist[0]*.28,a[1]*.72+wrist[1]*.28)
            cb=(b[0]*.72+wrist[0]*.28,b[1]*.72+wrist[1]*.28)
            outline.extend(bezier(a,ca,cb,b,15)[1:])
        outline.append(sh)
        poly(outline,WING_DARK if far else WING,INK,2.6)
        for k,(a,b) in enumerate(zip(tips,tips[1:])):
            a1=(wrist[0]*.37+a[0]*.63,wrist[1]*.37+a[1]*.63)
            b1=(wrist[0]*.37+b[0]*.63,wrist[1]*.37+b[1]*.63)
            mid=((a1[0]+b1[0])*.5,(a1[1]+b1[1])*.5)
            poly([wrist,a1,mid,b1], '#48384c' if far else (WING_LIGHT if k%2==0 else '#584457'),None)
        limb([sh,W(-31,-25-7*beat),wrist],[7,5,3.9],FAR if far else SKIN,None if far else LIGHT)
        for k,tip in enumerate(tips[:-1]):
            line([wrist,((wrist[0]+tip[0])*.5,(wrist[1]+tip[1])*.5),tip],INK,3.6 if k==0 else 2.5)
            if not far:
                line([wrist,((wrist[0]+tip[0])*.53,(wrist[1]+tip[1])*.53)],'#857080',1.2)
        poly([W(-66,-57-15*beat),thumb,W(-52,-62-15*beat),wrist],HORN_DARK if far else HORN,INK,1.5)
    wing(True)
    wing(False)

    def leg(far):
        sway=math.sin(p+(math.pi if far else 0))
        hip=(8,29) if far else (-14,29)
        knee=(28+3*sway+6*death,45-5*q.charge+7*death) if far else (9+3*sway-7*death,47-5*q.charge+5*death)
        ankle=(17+2*sway+4*death,66-5*q.charge+13*death) if far else (-15+2*sway-6*death,69-5*q.charge+10*death)
        col=FAR if far else SKIN
        limb([hip,((hip[0]+knee[0])*.5-2,(hip[1]+knee[1])*.5),knee,ankle], [10,12,7.8,5.5],col,None if far else LIGHT)
        x,y=ankle
        # Three hooked toe claws, not a shoe or hoof silhouette.
        shape((x-7,y-3),((x+2,y-7),(x+10,y-3),(x+15,y+2)),
              ((x+16,y+8),(x+7,y+11),(x-4,y+9)),
              ((x-9,y+7),(x-10,y+1),(x-7,y-3)),fill=col)
        for k in range(3):
            xx=x+3+k*4
            poly([(xx,y+4),(xx+5,y+5),(xx+5,y+12),(xx+1,y+9)],HORN_DARK if far else CLAW,INK,1.1)
    leg(True)

    def arm(far):
        s=math.sin(p+(1.0 if far else 0))
        if far:
            shoulder=(22,-28)
            elbow=(43+5*q.charge+7*death,0+3*s+4*death)
            wrist=(56+5*q.charge+7*q.shoot+11*death,13-10*q.charge-5*q.shoot+18*death)
        else:
            shoulder=(-24,-24)
            elbow=(-47-8*q.charge-6*recoil,-3+3*s+8*death)
            wrist=(-41-9*q.charge-18*death,25-7*q.charge+6*death)
        col=FAR if far else SKIN
        # A muscular bicep tapering into a long forearm.
        mid=((shoulder[0]+elbow[0])*.5-2,(shoulder[1]+elbow[1])*.5)
        fore=((elbow[0]+wrist[0])*.5,(elbow[1]+wrist[1])*.5)
        limb([shoulder,mid,elbow,fore,wrist],[10,13,8,9,5.7],col,None if far else LIGHT)
        x,y=wrist
        ang=math.degrees(math.atan2(y-elbow[1],x-elbow[0]))
        def H(u,v):return add(wrist,rot((u,v),ang))
        oval(*H(3,0),9,7,col,angle=ang)
        # Claws follow the palm and splay on the attack/death poses.
        spread=1.5+2.6*q.charge+3.2*death
        for k in range(3):
            v=(k-1)*5.0
            tip_v=v+(k-1)*spread
            reach=18-abs(k-1)*2+2*death
            shape(H(5,v-2),(H(10,v-2),H(reach,tip_v-2),H(reach,tip_v+1)),
                  (H(reach-3,tip_v+5),H(9,v+3),H(5,v+2)),
                  fill=HORN_DARK if far else CLAW, width=1.3)
        poly([H(0,-6),H(4,-12),H(11,-10),H(8,-5)],col,INK,1.4)
    # Canvas-right arm is FAR: behind body and face. The canvas-left arm
    # is painted over the torso but before the head, on its own side.
    arm(True)

    # Broad chest, narrow waist and heavy pelvic musculature. The highlight
    # shapes are facets of the same hide, not separate armor or clothes.
    shape((-22,-39),((-2,-46),(24,-42),(31,-27)),
          ((36,-13),(22,3),(17,13)),((13,24),(21,30),(14,37)),
          ((1,43),(-16,41),(-25,31)),((-30,18),(-22,9),(-28,-3)),
          ((-39,-13),(-37,-29),(-22,-39)),fill=SKIN,width=2.8)
    shape((-24,-29),((-14,-36),(1,-34),(9,-24)),
          ((12,-15),(3,-8),(-8,-7)),((-19,-7),(-27,-16),(-24,-29)),fill=LIGHT,edge=None)
    shape((12,-30),((24,-33),(30,-26),(30,-18)),
          ((26,-8),(16,-9),(10,-12)),((8,-19),(10,-26),(12,-30)),fill='#655d6e',edge=None)
    line([(-21,-7),(-9,-2),(5,-7),(16,-10)],SHADE,2.7)
    shape((-10,2),((0,-1),(13,-1),(14,9)),((10,17),(10,28),(0,30)),
          ((-14,30),(-19,14),(-10,2)),fill='#655e69',edge=None)
    for y in (7,15,23):
        line([(-12,y),(-3,y+3),(7,y)],SHADE,1.9)
    # Bony shoulder ridges echo the horn geometry, without adding armor.
    poly([(-32,-21),(-37,-33),(-27,-30),(-20,-23)],SHADE,INK,1.3)
    poly([(23,-30),(28,-42),(31,-32),(31,-23)],FAR,INK,1.3)
    leg(False)
    # A small overlapping hip plane hides the cap of the near thigh.
    shape((-23,26),((-19,20),(-5,22),(-1,30)),
          ((1,37),(-9,41),(-19,38)),((-24,35),(-25,30),(-23,26)),
          fill=SKIN,edge=None)
    arm(False)

    # Adult head: swept ram-like horns, flatter cranial silhouette, heavy
    # brow, narrow angular jaw and multiple fangs. No arm crosses the eyes.
    head_y=-2*q.charge-4*death
    def F(x,y):return (x,y+head_y)
    def fpoly(pts,fill,edge=INK,width=2):poly([F(*v) for v in pts],fill,edge,width)
    def fline(pts,fill=INK,width=1.8):line([F(*v) for v in pts],fill,width)
    def foval(x,y,rx,ry,fill,edge=INK,width=1.6,angle=0):oval(x,y+head_y,rx,ry,fill,edge,width,angle)
    def fshape(start,*segs,fill,edge=INK,width=2):
        shape(F(*start),*((F(*a),F(*b),F(*d)) for a,b,d in segs),fill=fill,edge=edge,width=width)
    def horn(x,y,far):
        def H(a,b):return (x+a,y+b)
        fshape(H(-9,7),(H(-15,-9),H(-34,-21),H(-36,-39)),
               (H(-24,-29),H(-11,-27),H(-3,-24)),
               (H(10,-17),H(14,1),H(8,6)),
               (H(3,11),H(-5,10),H(-9,7)),fill=HORN_DARK if far else HORN,width=2.4)
        for a,b,d,e in [(-10,-5,10,-9),(-17,-14,4,-18),(-23,-22,-8,-26),(-29,-30,-19,-31)]:
            fline([H(a,b),H((a+d)*.5,(b+e)*.5+2),H(d,e)],'#63555a',1.7)
        if not far:fline([H(-4,3),H(2,-8),H(-7,-19)],'#d0bba0',1.5)
    horn(21,-62,True)
    # Far ear and far horn are partially concealed behind the skull.
    fpoly([(21,-58),(49,-66),(39,-42),(22,-38)],FAR)
    fpoly([(27,-53),(43,-61),(36,-45)],'#574553',None)
    horn(-8,-66,False)
    fshape((-27,-60),((-14,-73),(13,-71),(28,-60)),
           ((36,-53),(32,-47),(38,-43)),((50,-41),(50,-31),(39,-29)),
           ((33,-19),(23,-14),(14,-13)),((-4,-13),(-24,-20),(-30,-35)),
           ((-35,-45),(-34,-55),(-27,-60)),fill=SKIN,width=2.7)
    # Raised cheekbone and forehead planes, harder/older than the round imp.
    fshape((-27,-55),((-19,-64),(1,-66),(16,-60)),
           ((7,-61),(-5,-56),(-13,-49)),((-21,-44),(-27,-49),(-27,-55)),fill=LIGHT,edge=None)
    fpoly([(-20,-39),(-8,-35),(8,-31),(0,-23),(-16,-27)],'#655b6c',None)
    fpoly([(-28,-53),(-61,-68),(-49,-37),(-27,-28)],SKIN)
    fpoly([(-34,-51),(-53,-61),(-44,-40),(-33,-36)],SHADE,None)
    fline([(-54,-61),(-44,-48),(-34,-42)],LIGHT,1.6)
    # Eyes have slanted upper lids, bright irises and small slit pupils.
    if recoil>.45:
        fline([(-12,-47),(-1,-42),(12,-46)],INK,3.5)
        fline([(21,-48),(30,-43),(34,-47)],INK,3)
        fline([(-15,-52),(-3,-51),(13,-46)],SHADE,4.5)
        fline([(19,-51),(34,-55)],SHADE,3.7)
    else:
        a=2*q.alert
        fpoly([(-15,-53-a),(13,-45-a),(8,-39+a),(-9,-41+a)],EYE,INK,2)
        fpoly([(21,-48-a),(35,-53-a),(34,-42+a),(24,-39+a)],EYE,INK,1.7)
        foval(4,-45,2.5,4.6+a*.3,'#302231',None)
        foval(31,-47,1.8,4.1+a*.3,'#302231',None)
        fline([(-18,-57-a),(-3,-54-a),(15,-46-a)],SHADE,5)
        fline([(20,-50-a),(35,-56-a)],SHADE,4)
    foval(43,-40,3.4,1.8,INK,None,angle=-8)
    fline([(32,-39),(36,-35),(42,-34)],SHADE,1.6)
    g=max(q.charge,q.shoot)
    if g>.03:
        fshape((8,-27),((14,-31),(31,-33),(38,-29)),((33,-19),(24,-15),(16,-16)),((8,-17),(5,-21),(8,-27)),fill='#834631',edge=None)
        foval(30,-25,10*g,7*g,EMBER,None)
    if q.shoot>.08 or death>.10 or q.hurt>.65:
        gape=max(q.shoot,death,q.hurt*.75)
        fshape((10,-29),((23,-30),(37,-33),(44,-33)),
               ((46,-22+2*gape),(37,-16+2*gape),(24,-17+2*gape)),
               ((14,-16),(9,-21),(10,-29)),fill='#2c1822',width=2.2)
        # lower jaw and pointed teeth follow mouth contour
        fpoly([(15,-29),(20,-29),(17,-22)],CLAW,INK,1)
        fpoly([(33,-31),(38,-32),(35,-24)],CLAW,INK,1)
        fpoly([(23,-17),(26,-23),(29,-17)],CLAW,INK,1)
        if q.shoot>.08:
            foval(38,-25,7*q.shoot,5*q.shoot,HOT,None)
        fline([(12,-19),(22,-15),(33,-17)],'#866774',1.5)
    else:
        fline([(7,-25),(17,-28),(31,-28),(42,-32)],INK,3.1)
        fpoly([(18,-28),(25,-28),(21,-20)],CLAW,INK,1)
        fpoly([(32,-29),(39,-31),(35,-23)],CLAW,INK,1)
        if q.charge>.05:
            fline([(18,-26),(30,-29),(41,-32)],EMBER,1.5+2*q.charge)
        fline([(2,-26),(7,-23)],SHADE,1.5)
    im=c.finish()
    if death>0:
        t=phase(i,n,False)
        # Keep the full silhouette through the contortion, then vanish.
        fade=min(1.,max(0.,(1-t)/.24))
        im.putalpha(im.getchannel('A').point(lambda a: round(a*fade)))
    return im


def render(out_dir: str | Path, **opts):
    del opts
    out=build_sheet(target=TARGET_NAME,rows=ROWS,render_fn=_render_frame,
        out_dir=Path(out_dir),frame_size=FRAME_SIZE,auto_crop=False,
        actor_metadata=ACTOR_METADATA,
        body_metrics_fn=lambda w,h:body_metrics_for_box(BODY_BOX,w,h),
        animation_key_map={name:name for name,_,_ in ROWS},
        pose_bodies='authored',sits_on_ground=False)
    return [out[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]
