"""One-Armed Bandit: a saloon slot machine that took up banditry.

The cabinet, three independently turning reels, single pull-lever arm and
cowboy boots carry the visual pun. No second arm or concealed weapon.
Locomotion and the lever's end targets use the shared point-based IK solver.
The payout in attack_side is a local visual cue, not a gameplay projectile.
"""
from __future__ import annotations

import math
from pathlib import Path
from dataclasses import dataclass, replace

from PIL import Image, ImageDraw

from ...authoring.sheet_build import build_sheet
from ...authoring.skeleton import (
    BoneWorld, PartCtx, Channel, draw_polygon, rotate_point, two_bone_ik_points,
)
from ...authoring.rig import add, vec, clamp, smoothstep, lerp
from ...core.draw import font, resize_transparent_sprite, rgba
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'one_armed_bandit'
FRAME_SIZE = (410, 350)
SUPER = 3
ORIGIN = (155.0, 254.0)
GROUND = 319.0
BODY_BOX = (80, 101, 230, 320)
ROWS = [
    ('idle', 10, 110), ('walk', 16, 75), ('dash', 10, 65),
    ('notice', 8, 75), ('windup', 12, 70), ('attack_side', 20, 65),
    ('hit', 7, 70), ('death', 16, 85),
]
LOOPS = {'idle', 'walk', 'dash'}
ACTOR_METADATA = {
    'actor': {'character_id': TARGET_NAME, 'display_name': 'One-Armed Bandit'},
    'body': {'body_plan': 'Biped', 'body_kind': 'Standard', 'mass_class': 'Medium',
             'locomotion_hint': 'Walk', 'traits': ['western', 'mechanical', 'outlaw', 'slot_machine']},
    'visual': {'default_pose': 'idle', 'portrait': {'animation': 'idle', 'frame': 0}},
    'tags': ['enemy', 'western', 'mechanical'],
    'authoring_description': (
        'A brass and walnut three-reel saloon slot machine with a battered cowboy hat, '
        'bandana, spurred boots and exactly one articulated pull lever. The arm cranks '
        'its own mechanism, the reels spin and stop, and a payout erupts from its coin '
        'tray. The visual coins are not gameplay projectiles. The actual attack, economy '
        'and faction rules belong to game content.'),
    'animation_bindings': {
        'default': {'animation': 'idle', 'events': []},
        'locomotion.walk': {'animation': 'walk', 'events': []},
        'combat.hurt': {'animation': 'hit', 'events': []},
        'combat.death': {'animation': 'death', 'events': []},
    },
}

INK='#231c20'; DARK='#393035'; BLACK='#29282b'
BRASS='#a77843'; GOLD='#d8af65'; LIT='#f2d89b'; SHADE='#725039'
TEAL='#426a69'; TEAL_D='#304b50'; TEAL_L='#78a09a'
WOOD='#714535'; WOOD_D='#482e2a'; WOOD_L='#a36b44'
IRON='#657071'; STEEL='#b1b9ac'; STEEL_L='#e2dfc7'
LEATHER='#91603d'; LEATHER_D='#50362d'; TAN='#c8995e'; TAN_L='#e2bf81'
RED='#a54436'; RED_D='#692d2b'; RED_L='#e78c6d'; CREAM='#f3e2b6'


def part(img, origin, angle=0):
    """Shared bone-local drawing context for a rigid painted part."""
    return PartCtx(img, ImageDraw.Draw(img), BoneWorld(origin,angle,0), {}, SUPER, {})


def child(ctx, p, angle=0):
    return part(ctx.img, ctx.bw.to_world(p), ctx.bw.angle+angle)


def poly(ctx, pts, fill, outline=INK, w=1.4):
    draw_polygon(ctx.draw,ctx.pts(pts),fill,outline,ctx.L(w))


def line(ctx, pts, color, w=1):
    ctx.draw.line(ctx.pts(pts),fill=color,width=max(1,round(ctx.L(w))),joint='curve')


def box(ctx, x0,y0,x1,y1, fill, outline=INK,w=1.3,b=0):
    poly(ctx,[(x0+b,y0),(x1-b,y0),(x1,y0+b),(x1,y1-b),(x1-b,y1),(x0+b,y1),(x0,y1-b),(x0,y0+b)],fill,outline,w)


def oval(ctx, c, rx,ry,fill,outline=INK,w=1.2):
    poly(ctx,[(c[0]+rx*math.cos(k*math.tau/48),c[1]+ry*math.sin(k*math.tau/48)) for k in range(48)],fill,outline,w)


def arc(ctx,c,rx,ry,a,b,color,w=1):
    line(ctx,[(c[0]+rx*math.cos(lerp(a,b,k/32)),c[1]+ry*math.sin(lerp(a,b,k/32))) for k in range(33)],color,w)


def screw(ctx,c,r=2):
    oval(ctx,c,r,r,BRASS,INK,.65)
    arc(ctx,c,r-.5,r-.5,math.pi,1.7*math.pi,LIT,.65)
    line(ctx,[add(c,(-r*.55,-r*.35)),add(c,(r*.55,r*.35))],SHADE,.75)


def star(ctx,c,r,fill=GOLD):
    poly(ctx,[add(c,vec(r if j%2==0 else r*.43,-90+j*36)) for j in range(10)],fill,INK,.7)


def text(ctx, value, xy, size, color):
    """Small hardware lettering, rotated with the cabinet."""
    face=font(round(size*SUPER))
    bounds=face.getbbox(value)
    stamp=Image.new('RGBA',(max(1,bounds[2]-bounds[0]+6),max(1,bounds[3]-bounds[1]+6)))
    ImageDraw.Draw(stamp).text((3-bounds[0],3-bounds[1]),value,fill=color,font=face)
    stamp=stamp.rotate(-ctx.bw.angle,resample=Image.Resampling.BICUBIC,expand=True)
    x,y=ctx.pt(xy)
    ctx.img.alpha_composite(stamp,(round(x-stamp.width/2),round(y-stamp.height/2)))


@dataclass(frozen=True)
class Pose:
    x: float=0
    y: float=0
    tilt: float=0
    hat: float=0
    front: float=24
    rear: float=-27
    front_lift: float=0
    rear_lift: float=0
    arm_x: float=108
    arm_y: float=-126
    reel: float=0
    power: float=.6
    scarf: float=0
    collapse: float=0


# Each value is authored independently on the existing keyframe channel type.
# The attack starts at the windup's final pose and returns to idle.
TRACKS={
    'notice': {
        'tilt':Channel((0,0),(.3,-6),(.7,-2),(1,0)),
        'arm_x':Channel((0,108),(.5,105),(1,108)),
        'arm_y':Channel((0,-126),(.5,-105),(1,-126)),
        'hat':Channel((0,0),(.3,-5),(.8,2),(1,0)),
        'power':Channel((0,.6),(.5,1),(1,.8)),
    },
    'windup': {
        'y':Channel((0,0),(.3,4),(1,12)), 'tilt':Channel((0,0),(.35,-5),(1,-12)),
        'arm_x':Channel((0,108),(.35,111),(1,108)),
        'arm_y':Channel((0,-126),(.35,-72),(1,10)),
        'reel':Channel((0,0),(.25,.15),(1,5.5,'linear')),
        'power':Channel((0,.6),(.3,.9),(1,1)), 'hat':Channel((0,0),(.35,3),(1,-4)),
    },
    'attack_side': {
        'x':Channel((0,0),(.19,-4),(.39,12),(.61,7),(1,0)),
        'y':Channel((0,12),(.20,7),(.39,-5),(.50,5),(1,0)),
        'tilt':Channel((0,-12),(.18,-16),(.39,13),(.56,6),(1,0)),
        'arm_x':Channel((0,108),(.18,84),(.39,163),(.52,145),(.73,106),(1,108)),
        'arm_y':Channel((0,10),(.18,-131),(.39,-59),(.52,-32),(.73,-49),(1,-126)),
        'reel':Channel((0,5.5),(.35,11.5,'linear'),(.62,12.0),(1,12.0)),
        'power':Channel((0,1),(.38,1),(.55,.9),(1,.6)),
        'hat':Channel((0,-4),(.18,-8),(.43,13),(.70,-5),(1,0)),
        'scarf':Channel((0,0),(.2,-4),(.4,12),(.8,-3),(1,0)),
    },
    'hit': {
        'x':Channel((0,0),(.25,-12),(.62,-5),(1,0)),
        'tilt':Channel((0,0),(.25,-13),(.65,5),(1,0)),
        'y':Channel((0,0),(.25,9),(1,0)),
        'arm_x':Channel((0,108),(.4,116),(1,108)),
        'arm_y':Channel((0,-126),(.4,-40),(1,-126)),
        'hat':Channel((0,0),(.25,-19),(.65,9),(1,0)),
        'power':Channel((0,.6),(.25,.05),(.7,.9),(1,.6)),
    },
    'death': {
        'x':Channel((0,0),(.24,-8),(1,1)), 'y':Channel((0,0),(.27,8),(.8,37),(1,37)),
        'tilt':Channel((0,0),(.24,-14),(.8,49),(1,49)),
        'arm_x':Channel((0,108),(.23,118),(.80,145),(1,145)),
        'arm_y':Channel((0,-126),(.25,-15),(.8,-130),(1,-130)),
        'hat':Channel((0,0),(.3,-14),(.8,8),(1,8)),
        'reel':Channel((0,0),(.27,3.7),(.7,5.1),(1,5.1)),
        'power':Channel((0,.6),(.4,1),(.58,.05),(.7,.3),(.8,0),(1,0)),
        'collapse':Channel((0,0),(.3,.2),(.82,1),(1,1)),
        'front':Channel((0,24),(.25,39),(.333,60),(.4,75),(.4667,85),(.5333,90),(.6,95),(.6667,91),(.8,89),(1,89)),
    },
}


def step(phase, stride, lift):
    # A stance sweep then a raised return. Continuous position at loop seams.
    u=phase%1
    if u<.58:
        return lerp(stride,-stride,u/.58),0.
    s=(u-.58)/.42
    return lerp(-stride,stride,smoothstep(s)),lift*math.sin(math.pi*s)


def pose_for(anim,i,n):
    t=i/(n if anim in LOOPS else max(1,n-1)); p=Pose(); a=t*math.tau
    if anim=='idle':
        return replace(p,y=1.3*math.sin(a),tilt=.6*math.sin(a),hat=.9*math.sin(a-.6),
                       arm_x=108+2*math.sin(a),arm_y=-126+3*math.sin(a),scarf=1.8*math.sin(a-.9),power=.65+.12*math.sin(a))
    if anim in ('walk','dash'):
        dash=anim=='dash'; stride=24 if dash else 17; lift=15 if dash else 10
        x1,l1=step(t,stride,lift);x2,l2=step(t+.5,stride,lift)
        return replace(p, y=-2.5*abs(math.sin(a)), tilt=(11 if dash else 4)+1.7*math.sin(a),
                       front=17+x1,rear=-19+x2,front_lift=l1,rear_lift=l2,
                       arm_x=112+7*math.sin(a),arm_y=-114+10*math.sin(a),
                       hat=-3+3*math.sin(a-.8),scarf=(8 if dash else 3)+2*math.sin(a-.8))
    if anim not in TRACKS: raise ValueError(anim)
    p=replace(p,**{k:v.sample(t,False) for k,v in TRACKS[anim].items()})
    if anim=='death':
        p=replace(p,rear=-27-15*p.collapse)
    # Keep the rigid cabinet clear of the ground during the death collapse.
    # The boots and linkage have independent world-space targets.
    corners=[(-75,-3),(66,0),(49,10),(-55,10)]
    bottom=max(rotate_point(c,p.tilt)[1] for c in corners)
    p=replace(p,y=min(p.y,GROUND-ORIGIN[1]-bottom-3))
    return p


def cabinet_context(img,p):
    return part(img,add(ORIGIN,(p.x,p.y)),p.tilt)


def mechanical_link(ctx,a,b,width,bright=True):
    # Painted telescoping metal linkage; math for its joints lives in skeleton.py.
    line(ctx,[a,b],INK,width+4)
    line(ctx,[a,b],IRON if bright else TEAL_D,width)
    line(ctx,[add(a,(-2,-1)),add(b,(-2,-1))],STEEL if bright else IRON,max(1,width*.35))
    oval(ctx,a,width*.55,width*.55,BRASS if bright else SHADE,INK,1.2)
    screw(ctx,a,width*.24)


def boot(ctx,ankle,near,lift):
    q=child(ctx,ankle,-8 if lift>2 else 0)
    # Western boot: tall stitched leather shaft, angled heel, pointed toe, spur.
    base=LEATHER if near else LEATHER_D
    poly(q,[(-10,-24),(10,-24),(11,-7),(22,-2),(26,5),(21,9),(-3,9),(-9,6),(-12,9),(-16,9),(-16,0),(-11,-5)],base,INK,1.8)
    poly(q,[(-11,-24),(11,-24),(11,-20),(-10,-20)],TAN if near else SHADE,INK,.9)
    poly(q,[(-15,5),(-8,5),(-4,7),(22,7),(26,5),(23,10),(-3,10),(-7,8),(-15,10)],BLACK,INK,.9)
    line(q,[(-7,-18),(-1,-11),(5,-18)],GOLD if near else BRASS,1.1)
    line(q,[(-7,-15),(-6,-6),(7,-3),(19,1)],TAN_L if near else LEATHER,1.2)
    line(q,[(-14,-3),(-20,-3)],STEEL,2.5)
    star(q,(-21,-3),4.8,STEEL)
    oval(q,(-21,-3),1.2,1.2,IRON,INK,.5)


def draw_leg(world,body,p,near):
    root=body.bw.to_world((27 if near else -29,-1))
    x=p.front if near else p.rear; lift=p.front_lift if near else p.rear_lift
    target=(ORIGIN[0]+x,GROUND-11-lift)
    knee,ankle=two_bone_ik_points(root,target,39,38,bend=-1,fold_margin=.4,extension_margin=.5)
    mechanical_link(world,root,knee,13 if near else 11,near)
    mechanical_link(world,knee,ankle,10 if near else 8,near)
    boot(world,ankle,near,lift)


def reel_symbol(q,symbol,xy):
    r=child(q,xy)
    if symbol=='7':
        poly(r,[(-11,-9),(11,-9),(11,-4),(5,1),(1,10),(-6,10),(-2,0),(4,-4),(-11,-4)],RED,RED_D,.8)
        line(r,[(-8,-7),(8,-7)],RED_L,1.3)
    elif symbol=='cherry':
        line(r,[(-6,0),(0,-10),(8,0)],TEAL,2)
        poly(r,[(0,-10),(7,-12),(11,-9),(5,-6)],TEAL_L,TEAL_D,.7)
        oval(r,(-7,4),6,6,RED,RED_D,.8);oval(r,(7,4),6,6,RED,RED_D,.8)
        oval(r,(-9,2),1.6,1.8,RED_L,None);oval(r,(5,2),1.6,1.8,RED_L,None)
    elif symbol=='shoe':
        arc(r,(0,0),9,10,0,math.pi,BRASS,6)
        line(r,[(-9,-8),(-9,0)],BRASS,6);line(r,[(9,-8),(9,0)],BRASS,6)
        arc(r,(0,0),9,10,.12,math.pi-.12,LIT,1)
        for a in (.4,1.1,2,2.7):oval(r,vec(9,math.degrees(a)),1.1,1.1,INK,None)
    else:
        star(r,(0,0),11,GOLD)


def draw_reels(q,p):
    # Real bounded reel windows, rendered into a clipped local layer before
    # rigid rotation. Symbols travel together rather than blink between poses.
    for i,cx in enumerate((-30,5,40)):
        box(q,cx-16,-104,cx+16,-62,BLACK,BRASS,2,b=3)
        # Local clip: use an independent window then map it onto the body.
        rw,rh=27,36; img=Image.new('RGBA',(rw*SUPER,rh*SUPER),rgba(CREAM))
        r=part(img,(rw/2,rh/2))
        wheel=p.reel+math.sin(p.reel*math.pi/12)*i*.8
        # At rest show 7, cherry, horseshoe. During a payout each drum stops
        # at a discrete symbol, including after a fractional rotation.
        symbols=('7','cherry','shoe','star'); phase=wheel+i
        ix=math.floor(phase); frac=phase-ix
        for j in (-1,0,1,2):
            reel_symbol(r,symbols[(ix+j)%4],(0,(j-frac)*24))
        shade=Image.new('RGBA',img.size); sd=ImageDraw.Draw(shade)
        for y in range(6*SUPER):
            a=round(92*(1-y/(6*SUPER)));sd.line((0,y,rw*SUPER,y),fill=(72,50,38,a));sd.line((0,rh*SUPER-1-y,rw*SUPER,rh*SUPER-1-y),fill=(72,50,38,a))
        img.alpha_composite(shade)
        img=img.rotate(-q.bw.angle,Image.Resampling.BICUBIC,expand=True)
        x,y=q.pt((cx,-83));q.img.alpha_composite(img,(round(x-img.width/2),round(y-img.height/2)))
        line(q,[(cx-13,-100),(cx-13,-66)],'#fff1cd',.7)
    # Payline indicators, engraved not hovering.
    poly(q,[(-51,-86),(-46,-83),(-51,-80)],RED,INK,.7)
    poly(q,[(61,-86),(56,-83),(61,-80)],RED,INK,.7)


def draw_cabinet(q,p):
    # Left side is walnut, front is cast iron/brass; the front face is wide
    # enough that the slots read even at actual game size.
    poly(q,[(-68,-132),(-48,-153),(47,-153),(66,-131),(66,0),(49,10),(-55,10),(-75,-3),(-75,-119)],WOOD_D,INK,2.5)
    poly(q,[(-75,-119),(-59,-137),(-49,-144),(-49,2),(-55,10),(-75,-3)],WOOD,INK,1.5)
    for y in range(-116,-6,12):
        line(q,[(-71,y),(-65,y-4),(-57,y-5),(-51,y-7)],WOOD_L,.85)
    poly(q,[(-51,-137),(-35,-150),(40,-150),(62,-134),(66,-6),(52,6),(-49,6)],TEAL_D,INK,2)
    poly(q,[(-46,-133),(-31,-144),(37,-144),(58,-131),(60,-10),(48,0),(-45,0)],BRASS,INK,1.8)
    poly(q,[(-40,-127),(-27,-138),(34,-138),(52,-127),(54,-14),(44,-5),(-39,-5)],TEAL,INK,1.3)
    line(q,[(-47,-132),(-31,-146),(37,-146),(59,-132)],LIT,2.0)
    line(q,[(61,-127),(63,-8),(50,3)],SHADE,2.4)
    # Ornate marquee: three stars above a slot-machine nameplate.
    poly(q,[(-41,-131),(-24,-139),(34,-139),(52,-131),(52,-110),(-41,-110)],BLACK,BRASS,1.7)
    for x in (-28,5,38):star(q,(x,-131),4.5,GOLD if p.power>.15 else SHADE)
    text(q,'JACKPOT',(5,-119),10,LIT if p.power>.1 else BRASS)
    draw_reels(q,p)
    # Riveted brass rail and denomination plate. No face on the reels.
    box(q,-43,-58,52,-49,BRASS,INK,1.2,b=2)
    text(q,'5c',(5,-53.5),6.5,BLACK)
    # Coin slot + release button and the payout tray.
    box(q,-37,-43,-17,-23,BRASS,INK,1.3,b=3)
    box(q,-30,-40,-24,-26,BLACK,INK,.8,b=1)
    line(q,[(-28,-39),(-28,-27)],STEEL,.8)
    oval(q,(34,-35),8,8,BRASS,INK,1.2);oval(q,(34,-35),5,5,RED if p.power>.2 else RED_D,INK,.8)
    oval(q,(32.5,-37),1.5,1.2,RED_L,None)
    # A bandana knotted to the left of the cabinet below the controls.
    poly(q,[(-48,-49),(-21,-47),(53,-47),(54,-43),(-1,-39),(-45,-41),(-56,-40)],RED_D,INK,1.3)
    poly(q,[(-44,-44),(-26,-41),(-3,-41),(-19,-21),(-29,-28),(-42,-34)],RED,INK,1.2)
    for x,y in [(-33,-39),(-24,-35),(-30,-31),(-18,-39)]:oval(q,(x,y),1.3,1.3,CREAM,None)
    tail=p.scarf
    poly(q,[(-49,-44),(-60,-47),(-76-tail,-38+tail*.3),(-69-tail,-34+tail*.3),(-83-tail,-28+tail*.2),(-53,-36)],RED,INK,1.1)
    oval(q,(-52,-43),7,5,RED_L,RED_D,1.1)
    # Coin return mouth and shallow tray with a few visible coins.
    box(q,-13,-29,47,-9,BLACK,BRASS,2.2,b=4)
    poly(q,[(-14,-16),(45,-16),(52,-8),(46,1),(-9,1),(-18,-6)],IRON,INK,1.3)
    poly(q,[(-8,-15),(41,-15),(46,-10),(-13,-10)],DARK,INK,.8)
    for x,y in [(0,-10),(10,-11),(25,-9),(34,-11)]:oval(q,(x,y),4.4,2.1,GOLD,SHADE,.6)
    poly(q,[(-18,-7),(52,-7),(46,1),(-9,1)],BRASS,INK,1.1)
    line(q,[(-15,-6),(49,-6)],LIT,1.4)
    for c in [(-44,-135),(51,-132),(-43,-61),(53,-61),(-41,-12),(49,-13)]:screw(q,c)
    # Empty opposite side: a decorative bolted panel, not a second limb.
    box(q,-71,-95,-58,-65,WOOD_D,BRASS,1,b=2)
    star(q,(-64.5,-80),4,BRASS)


def draw_hat(q,p):
    h=child(q,(3,-145),p.hat)
    # An unmistakable cattleman hat: pinched crown, creased top, broad
    # turned-up sides and a deep curved brim. The near brim casts a shadow.
    poly(h,[(-82,-5),(-92,-17),(-83,-21),(-63,-16),(-48,-11),(39,-12),(67,-18),(87,-26),(92,-19),(83,-7),(57,2),(13,8),(-37,7),(-65,3)],LEATHER_D,INK,2.1)
    poly(h,[(-84,-13),(-88,-21),(-77,-22),(-60,-18),(-44,-13),(40,-13),(65,-22),(83,-31),(88,-28),(84,-17),(59,-6),(16,0),(-43,-1),(-70,-4)],TAN,INK,1.8)
    poly(h,[(-47,-12),(-45,-38),(-36,-65),(-20,-74),(-5,-70),(7,-65),(22,-74),(38,-69),(45,-52),(51,-12),(31,-4),(-22,-3)],TAN,INK,2)
    poly(h,[(-44,-38),(-35,-63),(-19,-71),(-4,-65),(7,-59),(-3,-51),(-18,-56),(-31,-50)],LEATHER, None)
    poly(h,[(22,-72),(38,-67),(43,-52),(47,-17),(33,-11),(26,-47),(12,-61)],LEATHER,None)
    line(h,[(-34,-62),(-19,-68),(-5,-62),(7,-57),(21,-68),(34,-64)],TAN_L,1.8)
    line(h,[(-42,-36),(-43,-20),(-34,-11)],TAN_L,2.2)
    poly(h,[(-46,-26),(-19,-19),(22,-20),(47,-27),(50,-13),(26,-6),(-22,-6),(-47,-14)],LEATHER_D,INK,1.5)
    line(h,[(-43,-24),(-17,-17),(22,-18),(44,-24)],LEATHER,1.25)
    box(h,8,-22,21,-9,GOLD,INK,1.2,b=2);box(h,11,-19,18,-12,LEATHER_D,INK,.65,b=1)
    line(h,[(-73,-16),(-62,-12),(-48,-8)],TAN_L,1.9)
    line(h,[(55,-10),(72,-17),(83,-25)],TAN_L,1.6)
    line(h,[(-35,-47),(-30,-48),(-24,-46)],LEATHER_D,1)
    line(h,[(36,-36),(38,-30)],SHADE,1)


def draw_arm(world,q,p):
    # Exactly one shoulder socket. The red ball is the machine's pull knob
    # and the striking end of its only arm. Keep it attached to the solved tip.
    root=q.bw.to_world((65,-75)); target=q.bw.to_world((p.arm_x,p.arm_y))
    elbow,tip=two_bone_ik_points(root,target,55,54,bend=-1,fold_margin=3,extension_margin=.5)
    mechanical_link(world,root,elbow,12)
    mechanical_link(world,elbow,tip,8)
    oval(world,root,12,12,BRASS,INK,1.8);oval(world,root,8.5,8.5,IRON,INK,1.3)
    screw(world,root,4.7)
    oval(world,elbow,8.3,8.3,BRASS,INK,1.4);screw(world,elbow,3.1)
    oval(world,tip,11.2,11.2,RED_D,INK,1.9);oval(world,add(tip,(-1.3,-1.8)),9.1,9.1,RED,None)
    oval(world,add(tip,(-3.8,-4.1)),3.2,2.4,RED_L,None)
    arc(world,tip,9.5,9.5,.1,1.2,RED_L,.9)
    return root,elbow,tip


def coin(q,xy,angle,spin):
    c=child(q,xy,angle);rx=2.5+5.5*abs(math.cos(spin))
    oval(c,(0,0),rx,7,GOLD,SHADE,1)
    arc(c,(0,0),rx-1.3,5.5,math.pi,1.85*math.pi,LIT,1.1)
    if rx>4: line(c,[(0,-4),(0,4)],BRASS,1.1)


def effects(world,anim,t,p,n):
    if anim=='attack_side':
        for j,start in enumerate((.37,.42,.47,.52,.57)):
            age=t-start
            if age<0 or age>.43:continue
            u=age/.43
            launch=cabinet_context(world.img,pose_for(anim,round(start*(n-1)),n)).bw.to_world((40,-10))
            coin(world,add(launch,(10+u*(63+j*9),-math.sin(math.pi*u)*(28+j*6)-8*u)),u*180+j*18,u*math.tau*2+j)
        if .34<t<.56:
            k=math.sin(math.pi*(t-.34)/.22)
            q=cabinet_context(world.img,p); c=q.bw.to_world((5,-120))
            for j in range(6):
                a=-160+j*28;line(world,[add(c,vec(58,a)),add(c,vec(58+10*k,a))],LIT,1.4)
    elif anim=='death':
        # The reels lose power and loose coins spill from the existing tray.
        if t>.36:
            for j in range(5):
                u=clamp((t-.36)/.64,0,1)
                launch=cabinet_context(world.img,pose_for(anim,round(.36*(n-1)),n)).bw.to_world((36,-11))
                cx=lerp(launch[0],ORIGIN[0]+50+j*15,u)
                cy=lerp(launch[1],GROUND-10,u)-math.sin(math.pi*u)*(10+j*5)
                coin(world,(cx,cy),u*110+j*11,u*9+j)


def render_frame(anim,i,n):
    p=pose_for(anim,i,n);t=i/(n if anim in LOOPS else max(1,n-1))
    img=Image.new('RGBA',tuple(v*SUPER for v in FRAME_SIZE)); world=part(img,(0,0)); q=cabinet_context(img,p)
    draw_leg(world,q,p,False)
    draw_leg(world,q,p,True)
    draw_cabinet(q,p);draw_hat(q,p)
    draw_arm(world,q,p)
    effects(world,anim,t,p,n)
    return resize_transparent_sprite(img,FRAME_SIZE)


def _body_metrics(fw,fh):
    return body_metrics_for_box(BODY_BOX,fw,fh)


def render(out_dir: str | Path, **opts):
    del opts
    outputs=build_sheet(target=TARGET_NAME,rows=ROWS,render_fn=render_frame,out_dir=Path(out_dir),
                        frame_size=FRAME_SIZE,auto_crop=False,actor_metadata=ACTOR_METADATA,
                        body_metrics_fn=_body_metrics,pose_bodies='authored',
                        animation_key_map={name:name for name,_,_ in ROWS})
    return [Path(outputs[k]) for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent') if outputs.get(k)]


TARGETS={TARGET_NAME:{'render':render,'actor_metadata':ACTOR_METADATA}}
