"""Multi-Armed Bandit: heavyweight relative of the saloon slot machine.

Four organic, muscular arms grow from bolted shoulder collars on a large
four-reel cabinet. The two forward fists deliver an alternating heavy combo;
rear arms brace the machine. All six articulated limbs use the shared IK
solver. The smaller bandit's drawing primitives and reel symbols are reused
so the two targets have a common visual vocabulary without sharing poses.
Coins and strike streaks are presentation only, not damage or economy rules.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace
from pathlib import Path

from PIL import Image, ImageDraw

from ...authoring.sheet_build import build_sheet
from ...authoring.skeleton import Channel, rotate_point, two_bone_ik_points
from ...authoring.rig import add, clamp, lerp, smoothstep, vec
from ...core.draw import resize_transparent_sprite, rgba
from ...core.measure import body_metrics_for_box
from .one_armed_bandit import (
    SUPER, INK, BLACK, DARK, BRASS, GOLD, LIT, SHADE, WOOD, WOOD_D, WOOD_L,
    IRON, STEEL, STEEL_L, LEATHER, LEATHER_D, TAN, TAN_L, RED, RED_D, RED_L,
    CREAM, part, child, poly, line, box, oval, arc, screw, star, text,
    reel_symbol, coin, step, mechanical_link,
)

TARGET_NAME = 'multi_armed_bandit'
FRAME_SIZE = (620, 440)
ORIGIN = (293., 340.)
GROUND = 414.
# Deliberately excludes the hat brim, fists, payout, and loose cloth. This is
# an authored footprint, not an attempt to measure every moving extremity.
BODY_BOX = (183, 135, 403, 415)
ROWS = [
    ('idle', 12, 100), ('walk', 16, 85), ('dash', 12, 70),
    ('notice', 8, 80), ('windup', 14, 70), ('attack_side', 24, 65),
    ('hit', 8, 70), ('death', 18, 85),
]
LOOPS = {'idle', 'walk', 'dash'}
ACTOR_METADATA = {
    'actor': {'character_id': TARGET_NAME, 'display_name': 'Multi-Armed Bandit'},
    'body': {'body_plan': 'Biped', 'body_kind': 'Standard', 'mass_class': 'Heavy',
             'locomotion_hint': 'Walk', 'traits': ['western', 'mechanical', 'outlaw', 'slot_machine', 'four_armed']},
    'visual': {'default_pose': 'idle', 'portrait': {'animation': 'idle', 'frame': 0}},
    'tags': ['enemy', 'western', 'mechanical', 'heavy'],
    'authoring_description': (
        'A heavyweight four-reel saloon slot machine, wearing a dark cattleman hat and '
        'four enormous bare muscular arms with leather wrist wraps. Its brass-collared '
        'shoulders brace for an alternating two-fist punch. Reel motion, coins and '
        'impact streaks are art cues, not gameplay attacks or economy effects.'),
    'animation_bindings': {
        'default': {'animation': 'idle', 'events': []},
        'locomotion.walk': {'animation': 'walk', 'events': []},
        'combat.hurt': {'animation': 'hit', 'events': []},
        'combat.death': {'animation': 'death', 'events': []},
    },
}

OX = '#743e3b'; OX_LIGHT = '#a85c4a'; OX_DARK = '#492b2d'
GUNMETAL = '#394047'; GUNMETAL_LIGHT = '#5d6468'; HAT = '#474047'
HAT_LIGHT = '#74626a'; HAT_DARK = '#2f292e'
SKIN = '#d69a68'; SKIN_LIGHT = '#f4c393'; SKIN_SHADOW = '#a86148'
SKIN_DEEP = '#754337'; SKIN_LINE = '#8d503b'
FAR_SKIN = '#ae7353'; FAR_LIGHT = '#d49a70'; FAR_SHADOW = '#81503d'
CLOTH = '#446a6c'; CLOTH_LIGHT = '#78a09a'; CLOTH_DARK = '#2a4146'


@dataclass(frozen=True)
class Pose:
    x: float = 0
    y: float = 0
    tilt: float = 0
    hat: float = 0
    scarf: float = 0
    reel: float = 0
    power: float = .65
    front: float = 34
    rear: float = -44
    front_lift: float = 0
    rear_lift: float = 0
    # Hand targets are cabinet-local. ul/ll = upper/lower left (far side);
    # ur/lr = upper/lower right (near side). The two pairs have their own
    # shoulder sockets and independent pose channels.
    ulx: float = -172
    uly: float = -207
    llx: float = -194
    lly: float = -38
    urx: float = 174
    ury: float = -208
    lrx: float = 198
    lry: float = -38


BASE = Pose()

# Keyframe tracks use the same interpolation machinery as the One-Armed
# Bandit. Windup and attack endpoints match, including reel phase.
TRACKS = {
    'notice': {
        'y': Channel((0,0),(.35,-4),(1,0)),
        'tilt': Channel((0,0),(.35,-4),(1,0)),
        'hat': Channel((0,0),(.4,-5),(1,0)),
        'urx': Channel((0,174),(.4,185),(1,174)),
        'ury': Channel((0,-208),(.4,-222),(1,-208)),
        'lrx': Channel((0,198),(.4,204),(1,198)),
        'lry': Channel((0,-38),(.4,-50),(1,-38)),
        'power': Channel((0,.65),(.4,1),(1,.65)),
    },
    'windup': {
        'x': Channel((0,0),(.4,-5),(1,-9)),
        'y': Channel((0,0),(.5,8),(1,12)),
        'tilt': Channel((0,0),(.5,-5),(1,-9)),
        'hat': Channel((0,0),(.5,4),(1,-5)),
        'scarf': Channel((0,0),(.5,-6),(1,-3)),
        'urx': Channel((0,174),(.5,163),(1,133)),
        'ury': Channel((0,-208),(.5,-220),(1,-205)),
        'lrx': Channel((0,198),(.5,167),(1,154)),
        'lry': Channel((0,-38),(.5,-39),(1,-92)),
        'ulx': Channel((0,-172),(.5,-179),(1,-181)),
        'uly': Channel((0,-207),(.5,-188),(1,-180)),
        'llx': Channel((0,-194),(.5,-181),(1,-190)),
        'lly': Channel((0,-38),(.5,-46),(1,-62)),
        'reel': Channel((0,0),(.3,.6),(1,6,'linear')),
        'power': Channel((0,.65),(.4,.85),(1,1)),
        'front': Channel((0,34),(1,45)), 'rear': Channel((0,-44),(1,-53)),
    },
    'attack_side': {
        'x': Channel((0,-9),(.12,-13),(.25,14,'in'),(.43,3),(.55,-4),(.68,17,'in'),(.84,7),(1,0)),
        'y': Channel((0,12),(.13,7),(.25,1),(.44,9),(.55,12),(.68,1),(.85,5),(1,0)),
        'tilt': Channel((0,-9),(.13,-13),(.25,10),(.44,-2),(.55,-8),(.68,12),(.85,4),(1,0)),
        'hat': Channel((0,-5),(.13,-9),(.28,10),(.44,-4),(.55,-7),(.72,9),(1,0)),
        'scarf': Channel((0,-3),(.15,-5),(.28,13),(.43,3),(.55,-5),(.72,15),(1,0)),
        # Upper fist punches first, then retracts as lower fist drives out.
        'urx': Channel((0,133),(.13,130),(.25,232,'in'),(.32,235),(.47,147),(.68,153),(.85,178),(1,174)),
        'ury': Channel((0,-205),(.13,-211),(.25,-154),(.32,-145),(.47,-213),(.68,-212),(1,-208)),
        'lrx': Channel((0,154),(.25,163),(.43,148),(.55,132),(.68,230,'in'),(.75,234),(.87,207),(1,198)),
        'lry': Channel((0,-92),(.25,-65),(.43,-77),(.55,-87),(.68,-95),(.75,-83),(.87,-47),(1,-38)),
        # Far arms counterbalance rather than mirroring the striking arms.
        'ulx': Channel((0,-181),(.13,-195),(.25,-174),(.44,-191),(.68,-182),(1,-172)),
        'uly': Channel((0,-180),(.13,-202),(.25,-164),(.44,-196),(.68,-178),(1,-207)),
        'llx': Channel((0,-190),(.25,-209),(.44,-190),(.68,-214),(1,-194)),
        'lly': Channel((0,-62),(.25,-55),(.44,-69),(.68,-36),(1,-38)),
        'front': Channel((0,45),(.25,55),(.55,47),(.68,60),(1,34)),
        'rear': Channel((0,-53),(.25,-58),(.68,-57),(1,-44)),
        'reel': Channel((0,6),(.25,11,'linear'),(.5,14,'linear'),(.72,16),(1,16)),
        'power': Channel((0,1),(.25,1),(.45,.8),(.68,1),(1,.65)),
    },
    'hit': {
        'x': Channel((0,0),(.24,-13),(.62,-6),(1,0)),
        'y': Channel((0,0),(.24,8),(.65,4),(1,0)),
        'tilt': Channel((0,0),(.24,-11),(.62,4),(1,0)),
        'hat': Channel((0,0),(.26,-17),(.66,8),(1,0)),
        'urx': Channel((0,174),(.3,201),(1,174)),
        'ury': Channel((0,-208),(.3,-174),(1,-208)),
        'lrx': Channel((0,198),(.3,207),(1,198)),
        'lry': Channel((0,-38),(.3,-13),(1,-38)),
        'ulx': Channel((0,-172),(.3,-193),(1,-172)),
        'uly': Channel((0,-207),(.3,-160),(1,-207)),
        'llx': Channel((0,-194),(.3,-209),(1,-194)),
        'lly': Channel((0,-38),(.3,-19),(1,-38)),
        'power': Channel((0,.65),(.23,.06),(.5,.85),(1,.65)),
    },
    'death': {
        'x': Channel((0,0),(.22,-11),(.8,7),(1,7)),
        'y': Channel((0,0),(.2,9),(.8,48),(1,48)),
        'tilt': Channel((0,0),(.22,-9),(.83,19),(1,19)),
        'hat': Channel((0,0),(.22,-13),(.83,24),(1,24)),
        'scarf': Channel((0,0),(.22,-7),(.8,13),(1,13)),
        'front': Channel((0,34),(.3,55),(.83,85),(1,85)),
        'rear': Channel((0,-44),(.3,-58),(.83,-79),(1,-79)),
        'urx': Channel((0,174),(.26,199),(.82,158),(1,158)),
        'ury': Channel((0,-208),(.26,-163),(.82,-139),(1,-139)),
        'lrx': Channel((0,198),(.26,204),(.82,171),(1,171)),
        'lry': Channel((0,-38),(.26,-56),(.82,-62),(1,-62)),
        'ulx': Channel((0,-172),(.26,-202),(.82,-168),(1,-168)),
        'uly': Channel((0,-207),(.26,-160),(.82,-113),(1,-113)),
        'llx': Channel((0,-194),(.26,-214),(.82,-162),(1,-162)),
        'lly': Channel((0,-38),(.26,-48),(.82,-40),(1,-40)),
        'reel': Channel((0,0),(.33,3.6),(.7,5),(1,5)),
        'power': Channel((0,.65),(.23,1),(.38,.1),(.55,.65),(.75,0),(1,0)),
    },
}


def pose_for(anim, i, n):
    t = i / (n if anim in LOOPS else max(1,n-1))
    a = math.tau*t
    if anim == 'idle':
        s = math.sin(a); v = math.sin(a-.6)
        p = replace(BASE, y=1.4*s, tilt=.45*s, hat=.9*v, scarf=2*v,
                    urx=174+2*s, ury=-208-3*v, ulx=-172-2*s, uly=-207+3*v,
                    lrx=198+3*v, lry=-38+2*s, llx=-194-3*v, lly=-38-2*s,
                    power=.65+.08*s)
    elif anim in ('walk','dash'):
        dash = anim=='dash'; stride=25 if dash else 20; lift=14 if dash else 10
        x1,l1=step(t,stride,lift); x2,l2=step(t+.5,stride,lift)
        s=math.sin(a); v=math.cos(a)
        p=replace(BASE, y=-3*abs(s), tilt=(8 if dash else 3)+2*s,
                  front=29+x1,rear=-39+x2,front_lift=l1,rear_lift=l2,
                  urx=171+8*s,ury=-200+9*v,ulx=-174+6*s,uly=-195-9*v,
                  lrx=195-9*s,lry=-41+9*v,llx=-195-7*s,lly=-38-9*v,
                  hat=-2+2.7*math.sin(a-.7),scarf=(10 if dash else 4)+3*v)
    else:
        p=replace(BASE, **{k:v.sample(t,False) for k,v in TRACKS[anim].items()})
    # Keep the cabinet and its base above the ground during a heavy collapse.
    bottom=max(rotate_point(c,p.tilt)[1] for c in ((-112,0),(94,0),(78,9),(-89,9)))
    return replace(p,y=min(p.y,GROUND-ORIGIN[1]-bottom-3))


def body_context(img,p):
    return part(img,add(ORIGIN,(p.x,p.y)),p.tilt)


def heavy_boot(q, ankle, near, lift):
    b=child(q,ankle,-7 if lift>2 else 0)
    color=LEATHER if near else LEATHER_D
    poly(b,[(-14,-27),(14,-27),(16,-8),(29,-3),(34,4),(31,10),(-5,10),(-9,7),(-14,10),(-20,10),(-20,0),(-15,-7)],color,INK,2)
    poly(b,[(-15,-27),(14,-27),(15,-21),(-15,-21)],TAN if near else SHADE,INK,1.2)
    poly(b,[(-20,4),(-13,4),(-7,7),(30,7),(34,4),(31,11),(-4,11),(-10,8),(-19,11)],BLACK,INK,1)
    line(b,[(-10,-18),(0,-10),(10,-18)],GOLD if near else BRASS,1.7)
    line(b,[(-9,-14),(-8,-6),(9,-3),(27,2)],TAN_L if near else LEATHER,1.6)
    line(b,[(-17,-4),(-24,-4)],STEEL,3)
    star(b,(-25,-4),5.5,STEEL)
    oval(b,(-25,-4),1.6,1.6,IRON,INK,.6)


def draw_leg(world,q,p,near):
    root=q.bw.to_world((43 if near else -46,-3))
    x=p.front if near else p.rear; lift=p.front_lift if near else p.rear_lift
    target=(ORIGIN[0]+x,GROUND-12-lift)
    knee,ankle=two_bone_ik_points(root,target,46,45,bend=1 if near else -1,fold_margin=2,extension_margin=.5)
    mechanical_link(world,root,knee,19 if near else 16,near)
    mechanical_link(world,knee,ankle,15 if near else 13,near)
    oval(world,knee,10,10,BRASS if near else SHADE,INK,1.5); screw(world,knee,4)
    heavy_boot(world,ankle,near,lift)


def draw_reels(q,p):
    for i,cx in enumerate((-63,-21,21,63)):
        box(q,cx-19,-143,cx+19,-90,BLACK,BRASS,2.1,b=3)
        rw,rh=33,45
        img=Image.new('RGBA',(rw*SUPER,rh*SUPER),rgba(CREAM))
        r=part(img,(rw/2,rh/2))
        # Slight phase staggering, with integer positions at rest and at the
        # combo end. Window clipping is local, before cabinet rotation.
        phase=p.reel+i+math.sin(p.reel*math.pi/16)*i*.7
        ix=math.floor(phase); frac=phase-ix
        symbols=('7','cherry','shoe','star')
        for j in (-1,0,1,2):
            reel_symbol(r,symbols[(ix+j)%4],(0,(j-frac)*27))
        shade=Image.new('RGBA',img.size); sd=ImageDraw.Draw(shade)
        for y in range(8*SUPER):
            a=round(105*(1-y/(8*SUPER)))
            sd.line((0,y,rw*SUPER,y),fill=(72,50,38,a))
            sd.line((0,rh*SUPER-1-y,rw*SUPER,rh*SUPER-1-y),fill=(72,50,38,a))
        img.alpha_composite(shade)
        img=img.rotate(-q.bw.angle,Image.Resampling.BICUBIC,expand=True)
        x,y=q.pt((cx,-116.5)); q.img.alpha_composite(img,(round(x-img.width/2),round(y-img.height/2)))
        line(q,[(cx-16,-139),(cx-16,-94)],'#fff1cd',.7)
    for x,s in [(-85,1),(85,-1)]:
        poly(q,[(x,-121),(x+s*7,-116),(x,-111)],RED,INK,.8)


def draw_cabinet(q,p):
    # Heavy cast cabinet with broad shoulders, carved walnut side panels,
    # and an oxblood enamel face. The top is not a humanoid head.
    poly(q,[(-110,-166),(-90,-190),(-56,-205),(65,-205),(91,-183),(106,-158),(99,-7),(78,9),(-89,9),(-112,-5)],WOOD_D,INK,3)
    poly(q,[(-110,-166),(-89,-187),(-83,-197),(-82,-1),(-89,9),(-112,-5)],WOOD,INK,1.7)
    for y in range(-161,-9,13):
        line(q,[(-107,y),(-101,y-5),(-91,y-7),(-86,y-10)],WOOD_L,1.3)
    poly(q,[(-84,-188),(-58,-201),(62,-201),(91,-178),(98,-8),(77,5),(-83,5)],OX_DARK,INK,2.5)
    poly(q,[(-79,-183),(-55,-195),(59,-195),(85,-175),(91,-12),(74,0),(-78,0)],BRASS,INK,1.8)
    poly(q,[(-73,-178),(-52,-189),(57,-189),(79,-171),(84,-17),(69,-6),(-72,-6)],OX,INK,1.7)
    line(q,[(-80,-181),(-56,-197),(58,-197),(87,-177)],LIT,2.3)
    line(q,[(90,-169),(94,-10),(75,3)],SHADE,3)
    # Large Western marquee, with individually lit stars rather than eyes.
    poly(q,[(-75,-178),(-52,-189),(55,-189),(79,-171),(77,-150),(-75,-150)],BLACK,BRASS,1.8)
    for x in (-52,-26,0,26,52):
        star(q,(x,-180),5.2,GOLD if p.power>.15 else SHADE)
    text(q,'HIGH ROLLER',(2,-163),13,LIT if p.power>.1 else BRASS)
    draw_reels(q,p)
    # Reinforced rail and a copper denomination plate.
    box(q,-78,-85,79,-73,BRASS,INK,1.7,b=3)
    line(q,[(-73,-82),(73,-82)],LIT,1)
    text(q,'25c',(1,-78.5),8,BLACK)
    # Blue-green bandana sets this one apart from the red-scarfed light bandit.
    poly(q,[(-85,-73),(-59,-71),(83,-71),(84,-65),(5,-59),(-75,-62),(-91,-65)],CLOTH_DARK,INK,1.6)
    poly(q,[(-78,-68),(-49,-63),(-19,-63),(-38,-40),(-57,-50),(-74,-58)],CLOTH,INK,1.5)
    for x,y in [(-65,-63),(-52,-57),(-39,-60),(-43,-50)]:
        oval(q,(x,y),1.6,1.6,CREAM,None)
    s=p.scarf
    poly(q,[(-84,-66),(-98,-71),(-120-s,-61+s*.25),(-111-s,-54+s*.3),(-132-s,-45+s*.22),(-90,-57)],CLOTH,INK,1.5)
    oval(q,(-87,-65),8,6,CLOTH_LIGHT,CLOTH_DARK,1.2)
    # Heavy coin box, control plate, and payout opening.
    box(q,-65,-55,-44,-30,BRASS,INK,1.5,b=3)
    box(q,-58,-51,-51,-34,BLACK,INK,.8,b=2)
    line(q,[(-55,-48),(-55,-35)],STEEL,1)
    for x in (48,70):
        oval(q,(x,-48),8,8,BRASS,INK,1.2)
        oval(q,(x,-48),5,5,RED if p.power>.2 else RED_D,INK,.8)
        oval(q,(x-1.4,-50),1.5,1.3,RED_L,None)
    box(q,-41,-38,71,-11,BLACK,BRASS,2.4,b=5)
    poly(q,[(-42,-22),(71,-22),(81,-9),(74,2),(-35,2),(-49,-8)],IRON,INK,1.7)
    poly(q,[(-34,-20),(65,-20),(73,-11),(-43,-11)],DARK,INK,.9)
    for x,y in [(-25,-13),(-9,-14),(10,-13),(29,-13),(48,-12),(61,-14)]:
        oval(q,(x,y),5,2.6,GOLD,SHADE,.7)
    poly(q,[(-49,-9),(81,-9),(74,2),(-35,2)],BRASS,INK,1.5)
    line(q,[(-45,-8),(76,-8)],LIT,1.5)
    # Decorative rivets and lower cast-iron bumpers.
    for c in [(-79,-181),(79,-174),(-79,-147),(83,-147),(-78,-89),(80,-89),(-78,-18),(81,-19)]:
        screw(q,c,2.7)
    for x in (-66,68):
        box(q,x-13,-5,x+13,7,GUNMETAL,INK,1.3,b=2)
        line(q,[(x-9,-2),(x+9,-2)],GUNMETAL_LIGHT,1.5)


def draw_hat(q,p):
    h=child(q,(0,-193),p.hat)
    # A dark, broad-brimmed cattleman hat. Low pinched crown, exaggerated
    # upturned sides, gold hatband and a nick out of the right brim.
    poly(h,[(-107,-10),(-119,-26),(-112,-34),(-98,-29),(-67,-17),(-48,-15),(43,-15),(83,-23),(108,-37),(118,-34),(121,-24),(105,-10),(74,0),(21,8),(-45,8),(-83,0)],HAT_DARK,INK,2.8)
    poly(h,[(-112,-25),(-115,-33),(-103,-36),(-91,-31),(-63,-21),(-46,-18),(43,-18),(80,-27),(106,-41),(118,-37),(116,-30),(111,-23),(101,-25),(99,-16),(72,-7),(22,0),(-44,0),(-84,-10)],HAT,INK,2)
    poly(h,[(-54,-14),(-53,-45),(-43,-71),(-24,-83),(-8,-77),(5,-69),(19,-80),(39,-84),(51,-72),(59,-44),(61,-15),(39,-6),(-28,-5)],HAT,INK,2.6)
    poly(h,[(-49,-45),(-41,-69),(-24,-80),(-8,-73),(5,-65),(-9,-57),(-26,-63),(-39,-54)],HAT_LIGHT,None)
    poly(h,[(20,-78),(39,-81),(49,-70),(57,-44),(59,-18),(40,-9),(35,-48),(13,-63)],HAT_DARK,None)
    line(h,[(-42,-69),(-24,-77),(-8,-70),(5,-63),(20,-74),(38,-78),(48,-69)],HAT_LIGHT,2.1)
    line(h,[(-49,-41),(-50,-25),(-37,-14)],HAT_LIGHT,2.3)
    poly(h,[(-53,-31),(-26,-24),(33,-25),(58,-32),(61,-16),(36,-8),(-28,-7),(-54,-16)],LEATHER_D,INK,1.7)
    line(h,[(-49,-29),(-26,-22),(32,-23),(55,-29)],GOLD,1.6)
    box(h,5,-27,24,-10,BRASS,INK,1.3,b=3); star(h,(14.5,-18.5),6,LIT)
    line(h,[(-105,-29),(-90,-25),(-72,-18),(-57,-14)],HAT_LIGHT,2.3)
    line(h,[(63,-13),(82,-21),(99,-31),(109,-37)],HAT_LIGHT,2)
    line(h,[(37,-52),(42,-48),(44,-42)],HAT_LIGHT,1.5)


def angle_between(a,b):
    return math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))


def profile_points(length, sections, sign=1):
    """Smooth painted muscle contour; no kinematic calculation here."""
    pts=[]
    for (x0,r0),(x1,r1) in zip(sections,sections[1:]):
        for i in range(5):
            u=i/5; pts.append((length*lerp(x0,x1,u),sign*lerp(r0,r1,smoothstep(u))))
    x,r=sections[-1]; pts.append((length*x,sign*r)); return pts


def painted_muscle(q,length,upper,near,scale):
    """A tapered organic volume in bone-local coordinates, not a metal rod."""
    mid=SKIN if near else FAR_SKIN; lit=SKIN_LIGHT if near else FAR_LIGHT
    shade=SKIN_SHADOW if near else FAR_SHADOW
    top = [(-.05,14),(.12,23),(.33,26),(.54,23),(.76,17),(1.04,12)] if upper else [(-.07,12),(.13,19),(.37,20),(.59,15),(.84,11),(1.05,10)]
    bottom=[(-.05,14),(.17,20),(.39,23),(.61,20),(.83,15),(1.04,12)] if upper else [(-.07,12),(.16,17),(.39,18),(.63,14),(.87,10),(1.05,10)]
    top=[(x,r*scale) for x,r in top]; bottom=[(x,r*scale) for x,r in bottom]
    pts=profile_points(length,top,-1)+list(reversed(profile_points(length,bottom)))
    poly(q,pts,mid,INK,2.0)
    # Broad underside shadow follows the same outer contour.
    shade_pts=profile_points(length,bottom)+[(length*.95,2*scale),(length*.71,7*scale),(length*.47,11*scale),(length*.22,8*scale),(0,2*scale)]
    poly(q,shade_pts,shade,None)
    # Lit biceps and extensor planes, each a separate curved painted mass.
    if upper:
        poly(q,[(length*.04,-8*scale),(length*.14,-18*scale),(length*.28,-22*scale),(length*.44,-20*scale),(length*.59,-13*scale),(length*.63,-7*scale),(length*.48,-9*scale),(length*.32,-13*scale),(length*.18,-10*scale)],lit,None)
        line(q,[(length*.17,3*scale),(length*.35,8*scale),(length*.53,7*scale),(length*.70,2*scale)],SKIN_LINE,1.5)
        line(q,[(length*.68,-10*scale),(length*.81,-7*scale),(length*.9,-4*scale)],SKIN_LINE,1.3)
    else:
        poly(q,[(length*.06,-6*scale),(length*.19,-14*scale),(length*.35,-16*scale),(length*.54,-11*scale),(length*.73,-5*scale),(length*.43,-8*scale),(length*.22,-5*scale)],lit,None)
        line(q,[(length*.13,5*scale),(length*.34,7*scale),(length*.57,5*scale),(length*.79,2*scale)],SKIN_LINE,1.2)
        line(q,[(length*.46,-2*scale),(length*.71,-1*scale),(length*.89,2*scale)],lit,1.1)


def draw_fist(q,near,scale):
    # Fist extends along the forearm from the actual solved wrist. A closed
    # silhouette with knuckles, folded fingers, and opposing thumb.
    mid=SKIN if near else FAR_SKIN; lit=SKIN_LIGHT if near else FAR_LIGHT
    shade=SKIN_SHADOW if near else FAR_SHADOW
    def s(pts): return [(x*scale,y*scale) for x,y in pts]
    poly(q,s([(-6,-10),(1,-15),(13,-17),(23,-14),(28,-8),(30,1),(27,12),(18,16),(5,15),(-3,10)]),mid,INK,2)
    poly(q,s([(1,7),(11,10),(19,9),(28,4),(27,12),(18,16),(5,15),(-3,10)]),shade,None)
    poly(q,s([(3,-12),(12,-15),(22,-12),(24,-7),(14,-7),(7,-5)]),lit,None)
    # Four finger divisions and a folded thumb across the palm.
    for y in (-8,-2,4):
        line(q,s([(21,y),(27,y+1)]),SKIN_LINE,1.1)
    poly(q,s([(2,-3),(11,-6),(20,-3),(21,3),(15,7),(7,6),(2,2)]),mid,SKIN_LINE,1.3)
    line(q,s([(4,-2),(11,-4),(16,-2)]),lit,1.3)
    # Wide Western wrist wrap with stitching, before the first knuckle.
    poly(q,s([(-10,-12),(0,-13),(3,-11),(3,12),(-1,13),(-10,11)]),LEATHER_D,INK,1.4)
    line(q,s([(-7,-10),(-7,10)]),TAN,1.1)
    for y in (-7,0,7): line(q,s([(-5,y),(-2,y)]),GOLD,1)


def draw_arm(world,q,p,side,upper):
    near=side==1; tag=('u' if upper else 'l')+('r' if near else 'l')
    local_root=(side*(96 if upper else 99),-150 if upper else -63)
    root=q.bw.to_world(local_root)
    target=q.bw.to_world((getattr(p,tag+'x'),getattr(p,tag+'y')))
    # Upper arms are a little longer and thicker than the lower pair. The
    # sign picks an outward elbow on each side, consistently through a clip.
    a,b=(64.,61.) if upper else (58.,54.)
    bend=-side
    elbow,wrist=two_bone_ik_points(root,target,a,b,bend=bend,fold_margin=18,extension_margin=2)
    scale=1.0 if upper else .85
    if not near: scale*=.94
    # Shoulder collar is attached to the cabinet. A rounded deltoid overlaps
    # its inside edge, making a hybrid organic/mechanical joint.
    oval(world,root,23*scale,23*scale,BRASS if near else SHADE,INK,2)
    oval(world,root,18*scale,18*scale,GUNMETAL,INK,1.5)
    for k in range(4):
        screw(world,add(root,vec(20*scale,45+k*90)),2.3*scale)
    u=part(world.img,root,angle_between(root,elbow))
    oval(u,(12,0),21*scale,23*scale,SKIN if near else FAR_SKIN,INK,2)
    oval(u,(10,-7*scale),13*scale,10*scale,SKIN_LIGHT if near else FAR_LIGHT,None)
    painted_muscle(u,a,True,near,scale)
    lower=part(world.img,elbow,angle_between(elbow,wrist))
    painted_muscle(lower,b,False,near,scale)
    fist=part(world.img,wrist,angle_between(elbow,wrist))
    draw_fist(fist,near,scale*1.2)
    return root,elbow,wrist


def effects(world,q,p,anim,t,arms,n):
    if anim=='attack_side':
        # Two compact fist streaks. Never paint a disconnected fake punch.
        for tag,lo,hi in [('ur',.20,.34),('lr',.63,.77)]:
            if lo<t<hi:
                k=math.sin(math.pi*(t-lo)/(hi-lo))
                _,e,w=arms[tag]; a=angle_between(e,w)
                r=part(world.img,w,a)
                for y in (-21,-13,14,23):
                    line(r,[(-18-22*k,y),(6+13*k,y*.78)],LIT,1.8)
        for j,start in enumerate((.28,.32,.72,.76)):
            age=t-start
            if age<0 or age>.23: continue
            u=age/.23
            src=body_context(world.img,pose_for(anim,round(start*(n-1)),n)).bw.to_world((42,-15))
            coin(world,add(src,(8+(45+j*5)*u,-math.sin(math.pi*u)*(16+j*3))),u*110+j*19,u*8+j)
    elif anim=='death' and t>.4:
        for j in range(5):
            u=clamp((t-.4)/.6,0,1)
            src=body_context(world.img,pose_for(anim,round(.4*(n-1)),n)).bw.to_world((38,-15))
            dest=(ORIGIN[0]+46+j*17,GROUND-9)
            coin(world,(lerp(src[0],dest[0],u),lerp(src[1],dest[1],u)-math.sin(math.pi*u)*(9+j*3)),u*100+j*11,u*8+j)


def render_frame(anim,i,n):
    p=pose_for(anim,i,n); t=i/(n if anim in LOOPS else max(1,n-1))
    img=Image.new('RGBA',tuple(v*SUPER for v in FRAME_SIZE))
    world=part(img,(0,0)); q=body_context(img,p)
    draw_leg(world,q,p,False); draw_leg(world,q,p,True)
    # Left arms are behind the cabinet. The upper pair is drawn after the
    # lower pair so its biceps and fist remain legible at overlaps.
    draw_arm(world,q,p,-1,False); draw_arm(world,q,p,-1,True)
    draw_cabinet(q,p); draw_hat(q,p)
    lr=draw_arm(world,q,p,1,False); ur=draw_arm(world,q,p,1,True)
    effects(world,q,p,anim,t,{'lr':lr,'ur':ur},n)
    return resize_transparent_sprite(img,FRAME_SIZE)


def _body_metrics(fw,fh):
    return body_metrics_for_box(BODY_BOX,fw,fh)


def render(out_dir: str | Path, **opts):
    del opts
    out_dir=Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs=build_sheet(target=TARGET_NAME,rows=ROWS,render_fn=render_frame,out_dir=Path(out_dir),
                        frame_size=FRAME_SIZE,auto_crop=False,actor_metadata=ACTOR_METADATA,
                        body_metrics_fn=_body_metrics,pose_bodies='authored',
                        animation_key_map={name:name for name,_,_ in ROWS})
    return [Path(outputs[k]) for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent') if outputs.get(k)]


TARGETS={TARGET_NAME:{'render':render,'actor_metadata':ACTOR_METADATA}}
