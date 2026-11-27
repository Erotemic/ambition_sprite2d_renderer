"""Argon (Ar, 18): a noble gas in regal protective robes.

The gas is colorless in its ordinary state. These emissive colors are a
stylized excited-argon discharge, not an intrinsic color or a calibrated
plasma spectrum. Selected air wavelengths (nm), NIST Strong Lines of Argon:
Ar I 415.859, 420.067, 696.543, 706.722; Ar II 434.806, 442.600.
https://physics.nist.gov/PhysRefData/Handbook/Tables/argontable2.htm
Gold and ivory belong to the costume, not the spectrum.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter

from ._clockwork_enemy_art import Canvas, add, sub, mul, mix, unit, perp, rot, bezier, phase, track
from ...authoring.skeleton import two_bone_ik_points
from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'argon_elemental'
FRAME_SIZE = (360, 300)
CENTER = (151., 146.)
WINDUP, ACTIVE, RECOVER = .64, .23, .83
TOTAL = WINDUP + ACTIVE + RECOVER
A, B = WINDUP / TOTAL, (WINDUP + ACTIVE) / TOTAL
ROWS = [('idle', 24, 65), ('walk', 24, 50), ('run', 24, 40),
        ('notice', 10, 65), ('windup', 16, 40), ('attack_side', 51, 33),
        ('hit', 9, 65), ('death', 24, 55), ('death_idle', 1, 200)]
LOOPS = {'idle', 'walk', 'run', 'death_idle'}
TRAITS = ['enemy', 'science', 'elemental', 'chemical_element', 'argon', 'noble_gas']
ACTOR_METADATA = {
    'actor': {'character_id': TARGET_NAME, 'display_name': 'Argon Elemental'},
    'body': {'body_plan': 'Floating', 'body_kind': 'Floating', 'mass_class': 'Light',
             'locomotion_hint': 'Fly', 'traits': TRAITS},
    'actions': {'default_preset': 'argon_elemental_displace'},
    'visual': {'default_pose': 'idle', 'portrait': {'animation': 'idle', 'frame': 0}},
    'animation_bindings': {
        'default': {'animation': 'idle', 'events': []},
        'locomotion.walk': {'animation': 'walk', 'events': []},
        'locomotion.run': {'animation': 'run', 'events': []},
        'combat.hurt': {'animation': 'hit', 'events': []},
        'combat.death': {'animation': 'death', 'events': []},
        'action.melee.primary': {'animation': 'attack_side', 'events': [
            {'t': A, 'event': 'hitbox_active_start', 'source': 'argon_elemental.displace'},
            {'t': B, 'event': 'hitbox_active_end', 'source': 'argon_elemental.displace'},
        ]},
    },
    'tags': TRAITS,
    'authoring_description': 'Argon, a smiling noble gas in violet and gold robes, with an Ar clasp and a flowing luminous discharge. Colorless ordinary argon is represented here by the colors of excited argon. Pure, Safe Argon! is its reassuring refrain.',
    'gameplay_description': 'A genial floating elemental that opens its arms and billows outward in an engulfing cloud. The current displacement lunge is unchanged. The local cloud is visual only; persistent world-space gas and containment are encounter mechanics for the engine.',
}

# Art-directed display colors inspired by the selected spectral lines.
# Pale tints suggest mixed emission and perceived brightness. Red accents
# remain narrow, so the gas silhouette retains its violet/blue identity.
VIOLET = '#7950e5'  # Ar I 415.859, 420.067 nm
BLUE = '#526df0'    # Ar II 434.806, 442.600 nm
RED = '#ec627b'     # Ar I 696.543, 706.722 nm, display-brightened
DEEP = '#32215e'
DARK = '#21163f'
MID = '#a68bf6'
LAV = '#cfbcff'
PALE = '#eef0ff'
GOLD = '#dfa64a'
GOLD_LIGHT = '#ffe6a3'
GOLD_DARK = '#8c5239'
CLOTH = '#433171'
CLOTH_LIGHT = '#6b4d9a'
CLOTH_DARK = '#282044'
IVORY = '#f5d7a7'


@dataclass(frozen=True)
class Pose:
    p: float = 0.
    move: float = 0.
    ready: float = 0.
    strike: float = 0.
    recover: float = 0.
    notice: float = 0.
    hurt: float = 0.
    death: float = 0.


def pose(anim, i, n):
    t = phase(i, n, anim in LOOPS)
    p = math.tau * (t % 1.)
    if anim == 'idle': return Pose(p)
    if anim in ('walk', 'run'): return Pose(p, move=.66 if anim == 'walk' else 1.)
    if anim == 'notice': return Pose(p, notice=track(t, [(0, 0), (.38, 1), (.78, 1), (1, 0)]))
    if anim == 'windup': return Pose(p, ready=track(t, [(0, 0), (.82, 1), (1, 1)]))
    if anim == 'attack_side':
        k = lambda keys: track(t, keys)
        flow = t / A if t <= A else 1 + (t-A)/(1-A)
        return Pose(math.tau * (flow % 1.),
                    ready=k([(0, 0), (.82*A, 1), (A, 1), (A+.04, 0), (1, 0)]),
                    strike=k([(0, 0), (A, 0), (A+.05, 1), (B, 1), (B+.14, .14), (1, 0)]),
                    recover=k([(0, 0), (B, 0), (B+.14, 1), (1, 0)]))
    if anim == 'hit': return Pose(p, hurt=math.sin(math.pi*t))
    if anim == 'death': return Pose(p, death=track(t, [(0, 0), (.2, .08), (.88, 1), (1, 1)]))
    if anim == 'death_idle': return Pose(death=1.)
    raise ValueError(anim)


def curve(start, *segments):
    pts = [start]
    for a, b, end in segments:
        pts.extend(bezier(pts[-1], a, b, end, n=14)[1:])
    return pts


def fill(c, P, start, segs, color, edge=None, w=1.6):
    c.poly([P(*p) for p in curve(start, *segs)], color, edge, w)


def stroke(c, P, start, segs, color, w=2.):
    c.line([P(*p) for p in curve(start, *segs)], color, w)


def _laurel(c, P, a, b, scale=1.):
    """Gold embroidery follows a local stem; no generated text or fonts."""
    stem = [mix(a, b, i/5) for i in range(6)]
    stem = [(x+4*math.sin(i*math.pi/5)*scale, y) for i, (x,y) in enumerate(stem)]
    c.line([P(*s) for s in stem], GOLD, 1.2*scale)
    for i in range(1,5):
        x,y = stem[i]
        for side in (-1,1):
            tip=(x+side*8*scale, y-5*scale)
            c.poly([P(x,y),P(x+side*6*scale,y+1.8*scale),P(*tip),P(x+side*2*scale,y-4*scale)], GOLD_LIGHT if side<0 else GOLD, None)


def _gas_tail(c,P,q):
    p=q.p; s=math.sin(p); v=math.cos(p); r=q.ready; h=q.strike
    drift=-15*q.move-17*h
    def T(x,y):
        f=max(0.,min(1.,(y-20)/95))
        return P(x+f*(drift+10*math.sin(p-y*.042)),y+f*4*math.cos(p-y*.04))
    # Rounded, folding wisps rather than a flame with pointy tongues.
    fill(c,T,(-42,17),[((-59,42),(-43,65),(-23,69)),((-5,74),(-1,91),(-25,101)),
         ((-37,107),(-15,116),(8,113)),((40,112),(57,94),(37,83)),((25,76),(34,67),(48,55)),
         ((68,37),(41,16),(22,16)),((2,13),(-24,13),(-42,17))],VIOLET,DEEP,1.8)
    fill(c,T,(-35,24),[((-47,45),(-33,57),(-10,64)),((13,72),(17,88),(-8,101)),
         ((11,111),(37,100),(31,90)),((15,79),(23,65),(38,53)),((51,39),(37,25),(13,23)),
         ((-3,20),(-22,18),(-35,24))],MID,None)
    fill(c,T,(-19,28),[((-29,49),(-7,55),(8,63)),((28,76),(15,87),(6,95)),
         ((29,83),(17,76),(28,62)),((45,44),(28,33),(10,30)),((0,26),(-12,22),(-19,28))],LAV,None)
    stroke(c,T,(-28,31),[((-35,53),(-10,58),(5,67)),((16,76),(13,84),(2,91))],PALE,3.6)
    stroke(c,T,(31,41),[((43,49),(15,65),(24,77)),((28,81),(43,89),(30,99))],BLUE,3.2)
    # A thin layer curls from the edge and rejoins the lower plume.
    fill(c,T,(-23,79),[((-42,70),(-48,83),(-42,92)),((-36,99),(-25,92),(-27,88)),
         ((-34,91),(-40,87),(-35,84)),((-30,82),(-25,84),(-23,79))],MID,DEEP,1.0)
    stroke(c,T,(-37,83),[((-42,86),(-38,92),(-32,91))],LAV,2.)
    stroke(c,T,(12,62+3*s),[((22,71),(25,79),(19,83+2*s))],PALE,2.2)
    # Fine red line emission within the blue-violet gas.
    stroke(c,T,(-27,48),[((-25,61),(-9,63),(-5,68))],RED,1.5)
    stroke(c,T,(6,103),[((16,108),(28,103),(31,100))],RED,1.4)
    for j in range(5):
        u=(p/math.tau+j/5)%1.; k=math.sin(math.pi*u)**1.3
        if k<.07:continue
        x=(-1 if j%2 else 1)*(25+25*u);y=76+27*u
        c.oval(T(x,y),4.7*k,2.8*k,LAV if j%2 else MID,None,angle=-20+40*u)


def _head(c,P,q):
    p=q.p; s=math.sin(p); v=math.cos(p); h=q.strike
    # One continuous gas silhouette, with expression formed directly in
    # its emissive material. No mask, visor, rim or separate face plate.
    fill(c,P,(-50,-48),[((-72,-70),(-59,-91),(-39,-97)),((-57,-112),(-27,-137),(-5,-128)),
         ((16,-124),(12,-110),(0,-109)),((-12,-116),(-1,-119),(6,-117)),
         ((29,-94),(62,-102),(67,-78)),((79,-59),(53,-39),(34,-36)),
         ((9,-25),(-36,-29),(-50,-48))],VIOLET,DEEP,2.)
    def F(x,y):
        a=max(0.,min(1.,(-y-60)/63))
        return P(x+a*6*math.sin(p+y*.055),y+a*4*math.cos(p+x*.045))
    fill(c,F,(-54,-72),[((-64,-95),(-40,-107),(-20,-102)),((-36,-117),(-15,-132),(2,-123)),
         ((10,-119),(1,-114),(-6,-113)),((10,-99),(21,-94),(40,-94)),
         ((66,-96),(73,-74),(56,-60)),((41,-49),(24,-54),(10,-61)),
         ((-13,-74),(-34,-68),(-54,-72))],MID,None)
    fill(c,F,(-47,-83),[((-37,-98),(-19,-96),(-9,-93)),((-27,-112),(-12,-127),(-1,-121)),
         ((-9,-117),(-4,-105),(11,-96)),((33,-87),(56,-92),(59,-77)),
         ((50,-82),(39,-80),(25,-82)),((-3,-87),(-20,-84),(-47,-83))],LAV,None)
    stroke(c,F,(-49,-82),[((-31,-94),(-16,-91),(6,-87)),((33,-77),(48,-83),(60,-70))],PALE,4.)
    stroke(c,F,(-40,-104),[((-31,-120),(-15,-130),(-3,-123))],BLUE,2.7)
    stroke(c,F,(26,-93),[((40,-94),(55,-94),(61,-87))],RED,1.7)
    # Outer vapor roll: a broad return curl and its cool rim.
    f=math.sin(p+.7)
    fill(c,F,(-47,-61),[((-75,-63),(-83,-82+3*f),(-66,-90)),
         ((-71,-78),(-57,-77),(-44,-81)),((-35,-81),(-30,-70),(-47,-61))],MID,DEEP,1.2)
    stroke(c,F,(-72,-82+3*f),[((-69,-70),(-56,-68),(-47,-73))],LAV,2.6)
    stroke(c,F,(51,-61),[((64,-57),(76,-63),(72,-74)),((65,-79),(62,-75),(64,-71))],LAV,2.6)
    # Soft, irregular density field across the bottom of the head. The
    # shading follows the gas mass, rather than an enclosed oval. Clip it
    # to the head alpha so it cannot create a second silhouette.
    shadow=Canvas(FRAME_SIZE,super_scale=c.s)
    fill(shadow,P,(-66,-69),[((-34,-87),(-7,-78),(22,-77)),
         ((49,-81),(65,-63),(68,-47)),((45,-26),(16,-26),(-12,-30)),
         ((-39,-33),(-64,-45),(-66,-69))],'#ffffff',None)
    mask=shadow.image.getchannel('A').filter(ImageFilter.GaussianBlur(9*c.s))
    mask=ImageChops.multiply(mask,c.image.getchannel('A')).point(lambda a:round(a*.77))
    shade=Image.new('RGBA',c.image.size,'#4930a1')
    shade.putalpha(mask)
    c.image.alpha_composite(shade)
    # Peripheral streams continue around the expressive area without forming
    # a face border. Keep the centre quiet enough for a small sprite.
    stroke(c,F,(-51,-55),[((-43,-43),(-33,-40),(-24,-43))],MID,2.5)
    stroke(c,F,(48,-66),[((60,-63),(55,-53),(50,-50))],LAV,2.2)
    stroke(c,F,(44,-42),[((51,-45),(57,-48),(59,-55))],RED,1.4)
    # Friendly crescent eyes are light within the gas itself. Windup uses
    # the same expression rather than replacing the eyes with display bars.
    blink=(abs(math.sin(p/2))>.997 and q.ready+q.strike+q.notice<.1) or q.hurt>.4
    eye_y=-60-1.5*q.ready
    for x in (-6,25):
        if blink:
            stroke(c,P,(x-7,eye_y),[((x-3,eye_y+3),(x+3,eye_y+3),(x+7,eye_y))],LAV,3.)
        else:
            segs=[((x-5,eye_y-12),(x+5,eye_y-12),(x+9,eye_y))]
            stroke(c,P,(x-9,eye_y),segs,LAV,4.5)
            stroke(c,P,(x-9,eye_y),segs,PALE,2.4)
    if q.hurt>.2:
        c.oval(P(10,-44),4.3,5.0,LAV,None)
    else:
        mouth=[((7,-36),(16,-36),(23,-45))]
        stroke(c,P,(-1,-45),mouth,LAV,4.0)
        stroke(c,P,(-1,-45),mouth,PALE,2.1)


def _arm(c,P,q,side):
    s=side; p=q.p; r=q.ready; h=q.strike
    shoulder=(s*31,-22)
    goal=(s*(70-20*r+6*math.sin(p+.9*s)+20*h+12*q.recover),
          1-19*q.notice-19*r-10*h-5*q.recover+4*math.cos(p+.7*s))
    elbow,wrist=two_bone_ik_points(shoulder,goal,27.,29.,bend=-s,extension_margin=.2)
    # Dress sleeve is a tapered contour following the solved joints.
    u=unit(sub(elbow,shoulder)); v=unit(sub(wrist,elbow)); n=perp(u); m=perp(v)
    a=add(shoulder,mul(n,12)); b=add(elbow,mul(n,15)); e=add(wrist,mul(m,10))
    a2=add(shoulder,mul(n,-12)); b2=add(elbow,mul(n,-15)); e2=add(wrist,mul(m,-10))
    pts=curve(a,(b,b,e),(add(e,mul(v,1)),add(e2,mul(v,1)),e2),(b2,b2,a2),(a2,a,a))
    c.poly([P(*a) for a in pts],CLOTH_DARK if s<0 else CLOTH,CLOTH_DARK,2.)
    stroke(c,P,add(shoulder,mul(n,6*s)),[(add(elbow,mul(n,8*s)),add(elbow,mul(m,7*s)),add(wrist,mul(m,6*s)))],CLOTH_LIGHT,3.)
    # Gold cuff, then a luminous open palm. Gas fingers are deliberately
    # soft and rounded, rather than a second rigid skeleton.
    c.poly([P(*add(e,mul(v,-5))),P(*e),P(*e2),P(*add(e2,mul(v,-5)))],GOLD,GOLD_DARK,1.2)
    a=math.degrees(math.atan2(v[1],v[0]))
    def H(x,y):return P(*add(wrist,rot((x,y),a)))
    fill(c,H,(0,-7),[((4,-10),(10,-13),(16,-11)),((21,-9),(16,-6),(13,-4)),
         ((20,-6),(26,-5),(25,-1)),((25,2),(18,3),(15,3)),((24,5),(25,8),(19,10)),
         ((15,10),(10,7),(8,7)),((12,13),(9,16),(5,13)),((1,9),(-1,4),(0,-7))],LAV,VIOLET,1.5)
    fill(c,H,(1,-5),[((6,-8),(10,-7),(13,-5)),((18,-1),(12,7),(5,6)),((1,4),(0,-2),(1,-5))],PALE,None)
    stroke(c,H,(8,2),[((12,0),(15,1),(17,3))],MID,1.6)
    return wrist


def _robes(c,P,q):
    p=q.p;r=q.ready;h=q.strike; f=math.sin(p); v=math.cos(p)
    def R(x,y):return P(x+max(0,y/78)*(-9*q.move-9*h+4*f),y+max(0,y/78)*(3*v-13))
    # Back cloak, visible in the spaces between hands and tail.
    fill(c,R,(-39,-24),[((-58,-4),(-53,27),(-70,54)),((-58,65),(-38,65),(-18,53)),
         ((0,72),(17,74),(36,53)),((55,66),(65,57),(74,46)),((50,22),(56,-4),(39,-24)),
         ((13,-35),(-13,-35),(-39,-24))],CLOTH_DARK,DARK,2.3)
    # Royal front panels. Continuous outer contour and crisp interior seams.
    fill(c,R,(-8,-9),[((-30,-21),(-48,-4),(-43,17)),((-41,39),(-54,59),(-49,74)),
         ((-29,71),(-11,49),(-3,27)),((5,8),(7,0),(-8,-9))],CLOTH, GOLD_DARK,2.)
    fill(c,R,(9,-10),[((27,-16),(41,-10),(47,9)),((51,31),(56,56),(65,67)),
         ((43,73),(22,53),(11,34)),((-4,13),(-3,0),(9,-10))],CLOTH_LIGHT,GOLD_DARK,2.)
    stroke(c,R,(-43,14),[((-42,37),(-53,62),(-49,74)),((-29,71),(-11,49),(-3,27))],GOLD,3.7)
    stroke(c,R,(47,9),[((50,30),(55,54),(65,67)),((43,73),(22,53),(11,34))],GOLD,3.7)
    stroke(c,R,(-34,19),[((-33,34),(-39,48),(-43,59))],CLOTH_LIGHT,2.1)
    stroke(c,R,(19,13),[((29,24),(36,44),(49,53))],'#9074ba',2.1)
    _laurel(c,R,(-39,58),(-20,24),.85)
    _laurel(c,R,(43,54),(26,20),.85)
    # A pair of broad ivory mantle panels, blue-purple yokes above them.
    fill(c,P,(-4,-28),[((-20,-49),(-43,-46),(-59,-32)),((-48,-23),(-42,-9),(-35,0)),
         ((-21,1),(-4,-9),(6,-20)),((4,-23),(1,-27),(-4,-28))],IVORY,GOLD_DARK,2.)
    fill(c,P,(12,-27),[((25,-45),(44,-46),(57,-34)),((46,-23),(49,-12),(56,-4)),
         ((43,3),(23,-7),(8,-20)),((9,-25),(10,-26),(12,-27))],IVORY,GOLD_DARK,2.)
    fill(c,P,(-3,-23),[((-19,-39),(-34,-37),(-49,-32)),((-42,-23),(-33,-17),(-26,-17)),
         ((-12,-15),(-4,-21),(-3,-23))],CLOTH,CLOTH_DARK,1.3)
    fill(c,P,(11,-23),[((28,-39),(43,-37),(49,-33)),((45,-24),(42,-18),(34,-16)),
         ((22,-16),(17,-20),(11,-23))],CLOTH,CLOTH_DARK,1.3)
    stroke(c,P,(-56,-31),[((-43,-19),(-38,-9),(-35,0)),((-20,0),(-3,-10),(6,-20))],GOLD,2.8)
    stroke(c,P,(57,-34),[((46,-23),(49,-12),(56,-4)),((43,3),(23,-7),(8,-20))],GOLD,2.8)
    # High turned collar and ribbon tails under the brooch.
    fill(c,P,(3,-28),[((-9,-48),(-39,-49),(-51,-40)),((-42,-43),(-25,-33),(-15,-23)),
         ((-7,-17),(0,-21),(3,-28))],GOLD_LIGHT,GOLD_DARK,1.5)
    fill(c,P,(10,-28),[((21,-48),(42,-48),(55,-40)),((42,-41),(27,-31),(22,-23)),
         ((15,-18),(11,-22),(10,-28))],GOLD_LIGHT,GOLD_DARK,1.5)
    c.poly([P(1,-17),P(-14,27),P(-1,19),P(4,30),P(10,-16)],CLOTH_DARK,GOLD_DARK,1.2)
    c.poly([P(12,-18),P(28,24),P(15,17),P(12,28),P(4,-17)],CLOTH,GOLD_DARK,1.2)
    # Periodic-table clasp: vector letters remain reproducible without fonts.
    c.oval(P(8,-20),14.5,16.5,GOLD_DARK,DARK,1.2)
    c.oval(P(8,-20),12.7,14.7,GOLD,None)
    c.oval(P(8,-20),9.8,11.6,DEEP,GOLD_LIGHT,1.)
    c.line([P(1,-15),P(5,-26),P(9,-15)],GOLD_LIGHT,1.6)
    c.line([P(3,-19),P(7,-19)],GOLD_LIGHT,1.4)
    c.line([P(11,-15),P(11,-22),P(14,-22),P(16,-20)],GOLD_LIGHT,1.4)
    c.disk(P(4,-32),1.6,PALE,None)


def _engulf_cloud(c,P,q,*,front=False):
    """Attached discharge only; not a world-space fog or a damage volume.

    Two translucent passes give the expansion depth without hiding the face.
    The attack envelope drives the plume even during the recovery. All
    effects fit inside the existing sprite canvas and collision is unchanged.
    """
    strength=max(q.strike,.82*q.recover)
    if strength<.015:return
    p=q.p; travel=q.strike+q.recover*.8
    cloud=Canvas(FRAME_SIZE,super_scale=c.s)
    # Curling billows travel outward from the lower robe and open palms.
    # Rear cloud is taller, while the near layer curls below the clasp.
    def C(x,y):
        return P(x*(.54+.46*strength)+14*travel,
                 y+3*math.sin(p+x*.065)*strength)
    if not front:
        fill(cloud,C,(-80,74),[((-109,65),(-117,47),(-97,31)),
             ((-114,17),(-103,-8),(-80,-8)),((-89,-30),(-62,-52),(-42,-33)),
             ((-17,-53),(7,-49),(23,-32)),((45,-55),(78,-47),(83,-23)),
             ((106,-35),(136,-22),(133,-1)),((155,-7),(176,12),(166,30)),
             ((192,37),(188,65),(161,77)),((135,97),(77,93),(37,92)),
             ((-1,101),(-57,94),(-80,74))],VIOLET,None)
        fill(cloud,C,(-87,48),[((-102,31),(-86,7),(-67,13)),
             ((-78,-6),(-53,-31),(-31,-15)),((-15,-35),(8,-26),(21,-13)),
             ((41,-34),(62,-19),(68,-4)),((90,-25),(122,-12),(117,9)),
             ((139,4),(163,21),(149,38)),((176,43),(159,66),(138,67)),
             ((71,80),(-41,87),(-87,48))],MID,None)
        for x,y,sz in [(-74,13,19),(-32,-18,18),(47,-18,18),(101,-5,16),(150,35,18)]:
            stroke(cloud,C,(x-sz,y+5),[((x-sz,y-sz),(x+sz*.65,y-sz),(x+sz*.7,y)),
                   ((x+sz*.5,y+8),(x+2,y+8),(x+1,y+2))],LAV,2.8)
        alpha=.58*strength
    else:
        fill(cloud,C,(-75,71),[((-91,58),(-77,35),(-54,43)),
             ((-53,22),(-24,23),(-12,39)),((8,18),(38,26),(46,45)),
             ((59,21),(85,19),(98,40)),((119,19),(147,32),(146,51)),
             ((170,46),(180,73),(157,83)),((102,105),(48,103),(8,95)),
             ((-24,104),(-64,91),(-75,71))],MID,None)
        fill(cloud,C,(-58,69),[((-70,56),(-48,43),(-31,51)),
             ((-25,34),(-3,33),(9,49)),((27,31),(51,41),(56,58)),
             ((78,34),(101,38),(110,53)),((133,37),(152,55),(147,68)),
             ((124,85),(54,92),(8,86)),((-17,94),(-43,83),(-58,69))],LAV,None)
        for x,y,sz in [(-37,52,15),(10,49,17),(76,54,18),(127,57,16)]:
            stroke(cloud,C,(x-sz,y+5),[((x-sz,y-sz),(x+sz*.75,y-sz),(x+sz*.7,y)),
                   ((x+sz*.5,y+8),(x+3,y+8),(x+1,y+2))],PALE,2.4)
        stroke(cloud,C,(57,84),[((80,89),(104,81),(122,76))],RED,1.4)
        alpha=.74*strength
    # Fade the full pass, not each constituent polygon, to avoid hard
    # overlapping alpha seams between the shapes forming the cloud.
    cloud.image.putalpha(cloud.image.getchannel('A').point(lambda a:round(a*alpha)))
    c.image.alpha_composite(cloud.image)


def _render_frame(anim,i,n):
    q=pose(anim,i,n); c=Canvas(FRAME_SIZE)
    if q.death>=1.:return c.finish()
    p=q.p; r=q.ready; h=q.strike
    center=add(CENTER,(-5*r+7*h-8*q.hurt,2.5*math.sin(p)-5*q.notice-3*r+3*h))
    lean=9*q.move-9*r+14*h-13*q.hurt+8*q.death
    def P(x,y):return add(center,rot((x*(1+.05*h-.04*r),y*(1-.04*h+.04*r)),lean))
    # The gas tail sits behind the clothing. The hand and face layers remain
    # deliberately separate: no arm or attack effect is painted over the face.
    _engulf_cloud(c,P,q)
    _gas_tail(c,P,q)
    _arm(c,P,q,-1)
    head=Canvas(FRAME_SIZE,super_scale=c.s)
    _head(head,P,q)
    c.image.alpha_composite(head.image)
    _robes(c,P,q)
    _arm(c,P,q,1)
    _engulf_cloud(c,P,q,front=True)
    # Small drifting emission filaments near the crown and tail. They are
    # tightly bounded and continuous at clip endpoints.
    for j in range(7):
        f=(p/math.tau+j/7)%1.; k=math.sin(math.pi*f)**1.1
        if k<.08:continue
        side=-1 if j%2 else 1
        x=side*(43+19*f); y=(-99+31*f) if j<4 else (56+45*f)
        c.line([P(x-side*7*k,y+3*k),P(x,y)],BLUE if j%3==0 else (RED if j%3==1 else LAV),1.1+1.3*k)
    im=c.finish()
    if q.death:
        im.putalpha(im.getchannel('A').point(lambda a:round(a*(1-q.death))))
    return im


def render(out_dir: str|Path,**opts):
    result=build_sheet(target=TARGET_NAME,rows=ROWS,render_fn=_render_frame,out_dir=Path(out_dir),
                       frame_size=FRAME_SIZE,auto_crop=False,actor_metadata=ACTOR_METADATA,
                       body_metrics_fn=lambda w,h:body_metrics_for_box((91,45,211,255),w,h),
                       animation_key_map={a:a for a,_,_ in ROWS},sits_on_ground=False)
    return [result[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]
