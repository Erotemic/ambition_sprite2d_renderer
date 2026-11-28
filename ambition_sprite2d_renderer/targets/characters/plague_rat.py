"""Plague rat: a heavy, ragged dungeon predator with a committed bite."""
from __future__ import annotations

import math
from pathlib import Path

from ._magic_character_art import Canvas, add, sub, mul, mix, unit, perp, rot, bezier, phase, track, anchored_death
from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'plague_rat'
FRAME_SIZE = (372, 232)
GROUND = 193.0
BODY_BOX = (113, 61, 298, 194)
ROWS = [('idle', 16, 90), ('walk', 16, 85), ('run', 16, 55),
        ('notice', 10, 55), ('windup', 8, 70), ('attack_side', 16, 50),
        ('hit', 8, 65), ('death', 20, 60), ('death_idle', 6, 150)]
LOOPS = {'idle', 'walk', 'run', 'windup', 'death_idle'}
TRAITS = ['enemy', 'fantasy', 'monster', 'rat', 'rodent', 'quadruped', 'plague']
ACTOR_METADATA = {
    'actor': {'character_id': TARGET_NAME, 'display_name': 'Plague Rat'},
    'body': {'body_plan': 'Quadruped', 'body_kind': 'Standard',
             'mass_class': 'Heavy', 'locomotion_hint': 'Walk', 'traits': TRAITS},
    'capabilities': {'traversal': {'walk': True}},
    'actions': {'default_preset': 'plague_rat_bite'},
    'visual': {'default_pose': 'idle', 'portrait': {'animation': 'idle', 'frame': 0}},
    'animation_bindings': {
        'default': {'animation': 'idle', 'events': []},
        'locomotion.walk': {'animation': 'walk', 'events': []},
        'locomotion.run': {'animation': 'run', 'events': []},
        'action.melee.primary': {'animation': 'attack_side', 'events': [
            {'t': 0.0, 'event': 'hitbox_active_start', 'source': 'plague_rat.bite'},
            {'t': .16/.80, 'event': 'hitbox_active_end', 'source': 'plague_rat.bite'}]},
        'combat.hurt': {'animation': 'hit', 'events': []},
        'combat.death': {'animation': 'death', 'events': []},
    },
    'tags': TRAITS,
    'authoring_description': 'A bulky, hunched rat with matted dark olive fur, a torn ear, patches of bare skin, yellow incisors and a thick scarred tail.',
    'gameplay_description': 'It stalks prey, raises its hackles and braces for a powerful lunging bite. The green-tinged saliva is cosmetic.',
}

INK = '#242326'
FAR_INK = '#363332'
FUR = '#514c40'
FUR_DARK = '#302f2a'
FUR_LIGHT = '#726e52'
FUR_PALE = '#a39873'
FAR = '#3e3b35'
FAR_LIGHT = '#5c5848'
BELLY = '#70664d'
SKIN = '#8b7470'
SKIN_LIGHT = '#b49a86'
SKIN_DARK = '#65524f'
TAIL = '#92796e'
TOOTH = '#d7bf7b'
EYE = '#cfd35d'
SICK = '#9ca05e'
SICK_LIGHT = '#c4be83'


def _curve(points):
    out = [points[0]]
    for k in range(1, len(points), 3):
        out.extend(bezier(out[-1], *points[k:k+3], n=16)[1:])
    return out


def _shape(c, points, fill, edge=INK, width=2.0):
    c.poly(_curve(points), fill, edge, width)


def _gait(t, stride, lift, stance):
    """Move a foot back on the ground, then forward in the air."""
    t %= 1.0
    if t < stance:
        return stride*(.5 - t/stance), 0.0
    s = (t-stance)/(1-stance)
    return stride*(-.5 + .5*(1-math.cos(math.pi*s))), -lift*math.sin(math.pi*s)


def _render_frame(anim, i, n):
    t = phase(i, n, anim in LOOPS)
    cyc = math.tau*t
    gait = stride = lift = pitch = bob = stretch = crouch = rear = strike = hurt = dead = 0.0
    mouth, sniff, ears, bristle = .18, 0.0, 0.0, .26
    lash = .32*math.sin(cyc)
    if anim == 'idle':
        bob = 1.3*math.sin(cyc)
        mouth = .26 + .09*math.sin(cyc-.4)
        sniff = math.sin(3*cyc)
    elif anim in ('walk', 'run'):
        gait = 1.0 if anim == 'walk' else 2.0
        stride, lift = (26, 7) if gait == 1 else (37, 12)
        bob = -1.6*math.sin(cyc)**2 if gait == 1 else -4.5*math.sin(cyc)**2
        stretch = 2.0*math.sin(cyc) if gait == 1 else 5*math.sin(cyc)
        pitch = 2*math.cos(cyc) if gait == 1 else 5*math.cos(cyc)
        lash = .7*math.sin(cyc-.5)
        ears = -.15 if gait == 1 else -.45
        sniff = .35*math.sin(cyc)
    elif anim == 'notice':
        rear = track(t, [(0,0),(.4,1),(1,.72)])
        ears = rear
        pitch = -9*rear
        bob = -3*rear
        mouth = .18+.27*rear
        sniff = .45*math.sin(cyc*3)
    elif anim == 'windup':
        crouch = .90+.10*math.sin(cyc)
        pitch = 4*crouch
        ears = -.8
        mouth = .70+.12*math.sin(cyc)
        bristle = 1.0
        lash = math.sin(cyc*2)
    elif anim == 'attack_side':
        strike = track(t, [(0,.85),(.12,1),(.25,.82),(.55,.32),(1,0)])
        stretch = 10*strike
        pitch = -5*strike
        bob = -5*strike
        ears = -.85*strike
        mouth = track(t, [(0,1),(.12,.92),(.23,.06),(.4,.29),(1,.18)])
        bristle = strike
        lash = .95*strike
    elif anim == 'hit':
        hurt = track(t, [(0,.70),(.2,1),(.65,.25),(1,0)])
        pitch = -11*hurt
        bob = -4*hurt
        mouth = .75*hurt
        ears = -hurt
        bristle = hurt
        lash = -hurt
    elif anim in ('death', 'death_idle'):
        dead = track(t, [(0,0),(.12,.18),(.4,.48),(.78,1),(1,1)]) if anim == 'death' else 1
        hurt = .6*math.sin(math.pi*min(1,t*2.2)) if anim == 'death' else 0
        pitch = -8*hurt + 4*dead
        mouth = track(t, [(0,.6),(.25,1),(.65,.72),(1,.48)]) if anim == 'death' else .48
        ears = -dead
        bristle = hurt
        lash = -.6*dead
    else:
        raise ValueError(anim)

    c = Canvas(FRAME_SIZE)
    origin = (182-8*crouch+12*strike-9*hurt-3*dead,
              127+bob+10*crouch+22*dead)

    def B(x,y):
        return add(origin, rot((x*(1.22+stretch*.009),y*(1.34-.23*crouch-.18*dead)), pitch))

    def body(pts, col, edge=INK, w=2):
        _shape(c,[B(x,y) for x,y in pts],col,edge,w)

    def bline(pts,col,w=1.2):
        c.line([B(x,y) for x,y in pts],col,w)

    def bpoly(pts,col,edge=INK,w=1.5):
        c.poly([B(x,y) for x,y in pts],col,edge,w)

    # The tail follows the rump. The entire tail is behind the body and legs.
    root = B(-43,9)
    end = B(-119,13-9*lash+17*dead)
    tail = _curve([root,B(-67,28),B(-99,32),B(-114,21),
                   B(-126,9-8*lash+20*dead),B(-116,2-10*lash+22*dead),end])
    left, right = [], []
    for j,p in enumerate(tail):
        f = j/(len(tail)-1)
        tangent = unit(sub(tail[min(j+1,len(tail)-1)],tail[max(j-1,0)]))
        rad = (7.8*(1-f)**.80 + 1.15)*(1+.07*math.sin(29*f))
        normal = perp(tangent)
        left.append(add(p,mul(normal,rad)))
        right.append(add(p,mul(normal,-rad)))
    c.poly(left+right[::-1],TAIL,INK,1.6)
    c.line([mix(a,b,.28) for a,b in zip(left,right)],SKIN_LIGHT,1.2)
    for j in range(2,len(tail)-1,2):
        c.line([mix(left[j],right[j],.09),mix(left[j],right[j],.92)],SKIN_DARK,1.05)
    c.poly([mix(left[10],right[10],.16),mix(left[13],right[13],.15),
            mix(left[15],right[15],.72),mix(left[12],right[12],.72)],'#73645a',None)

    def fur_limb(points, radii, col, light, edge, near):
        # Interpolate the whole limb before drawing its silhouette. The two
        # sides meet at a rounded wrist and the root merges into the torso.
        # There is no independent outline across the elbow or thigh.
        path, rs = [], []
        for k,(a,b) in enumerate(zip(points,points[1:])):
            before = points[max(0,k-1)]
            after = points[min(len(points)-1,k+2)]
            controls = (add(a,mul(sub(b,before),.13)),sub(b,mul(sub(after,a),.13)))
            samples = bezier(a,*controls,b,n=9)
            for j,q in enumerate(samples[:-1]):
                u=j/9
                path.append(q)
                rs.append(radii[k]*(1-u)+radii[k+1]*u)
        path.append(points[-1]);rs.append(radii[-1])
        sides = [[],[]]
        for k,(q,r) in enumerate(zip(path,rs)):
            tangent = unit(sub(path[min(k+1,len(path)-1)],path[max(k-1,0)]))
            for side,sign in zip(sides,(1,-1)):
                side.append(add(q,mul(perp(tangent),r*sign)))
        c.poly(sides[0]+sides[1][::-1],col,None)
        cut = 3 if near else 0
        for side in sides:
            c.line(side[cut:],edge,1.5)
        c.line([mix(a,b,.25) for a,b in zip(*sides)][4:-3],light,1.2)
        # A few short guard hairs follow the limb, not its bounding box.
        if near:
            for j in (6,12):
                q=path[j]
                c.line([q,add(q,mul(unit(sub(path[j+2],q)),4.4))],FUR_DARK,1.0)

    # Each foot has its own projected ground point. The two far legs are
    # painted before the torso. Each near leg is painted as a complete chain.
    def leg(front, near):
        col, shade, edge = (FUR,FUR_LIGHT,INK) if near else (FAR,FAR_LIGHT,FAR_INK)
        skin, skinlight = (SKIN,SKIN_LIGHT) if near else (SKIN_DARK,SKIN)
        top = B(29 if front else -27, 11 if front else 7)
        fx = (223 if front else 144) if near else (247 if front else 123)
        gy = GROUND if near else GROUND-13
        fy = gy-4
        if gait:
            offset = (0 if front else .55) + (0 if near else (.43 if gait==1 else .16))
            gx,dy = _gait(t+offset,stride,lift,.60 if gait==1 else .46)
            fx += gx
            fy += dy
        if rear and front:
            fx += 4*rear if near else 9*rear
            fy -= (15 if near else 22)*rear
        if strike:
            fx += (25 if front else -15)*strike
            fy -= (16 if front else 6)*strike
        if hurt:
            fx -= 8*hurt
            fy -= (7 if front else 3)*hurt
        if dead:
            target = ((259 if front else 182) if near else (238 if front else 149),gy-4)
            fx,fy = mix((fx,fy),target,dead)
            fy = min(fy,gy-4)
        foot = (fx,fy)
        # The hind thigh joins the rump with a broad root. The foreleg
        # has a slimmer shoulder and an elbow that bends behind the wrist.
        if front:
            knee = add(mix(top,foot,.43),(-10+3*strike,0))
            ankle = mix(knee,foot,.84)
            fur_limb([top,knee,ankle], [12.0 if near else 8.5,7.4,4.2], col,shade,edge,near)
        else:
            knee = add(mix(top,foot,.47),(13-3*dead,-3))
            ankle = add(mix(knee,foot,.70),(-9,-1))
            fur_limb([top,knee,ankle], [17 if near else 13,11.2 if near else 7.4,4.2],col,shade,edge,near)
        fur_limb([ankle,mix(ankle,foot,.55),foot], [4.1,3.6,2.9],skin,skinlight,edge,False)
        # Broad bare paw, four short toes. Draw claws after the paw.
        x,y = foot
        paw = [(x-7,y-3),(x+1,y-5),(x+11,y-4),(x+16,y),(x+13,y+4),
               (x-7,y+4),(x-9,y+1)]
        c.poly(paw,skin,edge,1.4)
        for k in range(3):
            px,py = x+7+k*3.0,y+.4+k*.3
            c.line([(px-2,py-1.3),(px,py+.9)],SKIN_DARK,.8)
            c.poly([(px,py),(px+4.3,py+1.1),(px,py+1.8)],TOOTH,edge,.65)

    leg(False,False)
    leg(True,False)

    # The arched back and heavy haunches form the main silhouette. The
    # shoulder is lower than the rump; short tufts follow the back contour.
    body([(-51,7),(-64,-11),(-55,-37),(-36,-39),
          (-21,-45),(-8,-34),(8,-36),
          (22,-44),(39,-39),(47,-15),
          (59,5),(41,25),(22,30),
          (4,36),(-13,32),(-29,31),
          (-44,29),(-52,23),(-51,7)],FUR,INK,2.7)
    body([(-53,-11),(-50,-32),(-36,-40),(-20,-37),
          (-8,-33),(1,-30),(10,-31),
          (25,-41),(37,-31),(39,-22),
          (28,-19),(18,-27),(6,-21),
          (-10,-20),(-22,-28),(-34,-24),
          (-42,-18),(-47,-14),(-53,-11)],FUR_LIGHT,None)
    body([(-47,12),(-42,25),(-28,29),(-17,28),
          (2,34),(22,29),(34,21),
          (42,17),(46,9),(46,2),
          (31,15),(11,17),(-1,16),
          (-21,21),(-33,15),(-47,12)],BELLY,None)
    # Matted, uneven guard hairs around the hump. The clumps do not change
    # identity between frames; they bristle as part of the windup.
    for j,(x,y) in enumerate([(-51,-23),(-43,-34),(-34,-40),(-25,-42),(-15,-40),(-5,-34),(5,-35),(15,-39),(25,-40),(34,-35),(41,-28)]):
        h = 4.5+(j%3)*1.7+8*bristle
        bpoly([(x-6,y+5),(x-4,y-h),(x+1,y-2),(x+5,y-h*.46),(x+7,y+4)],FUR_DARK,None)
    # Patches of missing fur, rendered as dry mottled skin (not open wounds).
    body([(-46,0),(-42,-10),(-31,-13),(-28,-7),
          (-24,-4),(-28,-1),(-26,6),
          (-34,10),(-40,5),(-46,0)],'#786960',FUR_DARK,1.2)
    for x,y in [(-41,-3),(-35,-6),(-33,2),(-38,4)]:
        c.oval(B(x,y),1.7,1.15,'#9b8872',None)
    body([(7,-23),(16,-30),(23,-27),(27,-22),
          (28,-17),(21,-12),(16,-14),
          (12,-10),(8,-15),(7,-23)],'#7f7061',FUR_DARK,1.1)
    for x,y,ang in [(-46,-17,25),(-35,-26,48),(-24,-20,33),(-11,-22,49),(-3,-12,25),(18,-18,46),(30,-24,67),
                    (-43,7,40),(-30,13,27),(-15,9,45),(-6,15,50),(7,7,37),(18,16,28),(30,9,60)]:
        end = add((x,y),rot((9,0),ang))
        bline([(x,y),end],FUR_DARK,1.6)
        bline([(x+1,y-2),add(end,(1,-2))],FUR_LIGHT,.95)
    # A few ratty fur clumps break the lower outline and emphasize the bulk.
    for x,y in [(-42,24),(-29,29),(-15,31),(3,33),(18,31),(30,24)]:
        bpoly([(x-5,y-2),(x+2,y+6),(x+4,y+1),(x+7,y-4)],FUR_DARK,None)
    leg(False,True)
    leg(True,True)

    # The face has its own pivot at the neck. The long snout and cheek
    # move together. The jaw opens about the cheek instead of scaling.
    headroot = B(34,-15)
    ha = pitch-13*rear+10*crouch-5*strike-10*hurt+28*dead+1.5*sniff
    def H(x,y):
        return add(headroot,rot((x*1.14,y*1.13),ha))
    def hshape(pts,col,edge=INK,w=1.8):
        _shape(c,[H(x,y) for x,y in pts],col,edge,w)
    def hpoly(pts,col,edge=INK,w=1.5):
        c.poly([H(x,y) for x,y in pts],col,edge,w)
    def hline(pts,col,w=1.2):
        c.line([H(x,y) for x,y in pts],col,w)
    def hov(x,y,rx,ry,col,edge=INK,w=1.4,angle=0):
        c.oval(H(x,y),rx,ry,col,edge,w,ha+angle)

    def ear(far):
        # The round ear folds back in the windup. A notch interrupts the rim.
        ctr = (-2,-23) if far else (-15,-15)
        ang = -18-24*ears-54*dead if far else -26-24*ears-60*dead
        def E(x,y):
            return H(*add(ctr,rot((x,y),ang)))
        scl = .70 if far else .88
        def epts(seq):
            return [E(x*scl,y*scl) for x,y in seq]
        # The near ear has lost a substantial piece of the upper rim; the
        # smaller far ear retains a continuous rounded shape.
        rim = [(-8,9),(-16,-5),(-14,-18),(-5,-21),
               (6,-24),(15,-15),(14,-9),
               (9,-10),(10,-4),(13,-3),
               (11,5),(1,12),(-8,9)] if far else [(-8,9),(-16,-5),(-14,-16),(-8,-20),
               (-6,-21),(-4,-21),(-3,-20),
               (-4,-16),(-7,-12),(-5,-10),
               (-1,-11),(1,-17),(3,-17),
               (11,-17),(14,-10),(13,-4),
               (11,5),(1,12),(-8,9)]
        _shape(c,epts(rim),FAR if far else FUR,FAR_INK if far else INK,1.8)
        inner = [(-6,6),(-12,-4),(-9,-15),(-5,-16),
                 (0,-11),(3,-12),(7,-10),
                 (8,-4),(6,3),(2,6),
                 (-1,8),(-4,8),(-6,6)]
        _shape(c,epts(inner),SKIN_DARK if far else SKIN,None)
        _shape(c,epts([(-4,6),(-7,-1),(-4,-7),(1,-10),
                       (-1,-2),(2,2),(4,4),
                       (1,7),(-1,8),(-4,6)]),FUR_DARK,None)
    ear(True)

    # Lower jaw. A lower incisor shows as the mouth opens.
    jaw_hinge = (9,12)
    def J(x,y):
        return H(*add(jaw_hinge,rot((x-jaw_hinge[0],y-jaw_hinge[1]),36*mouth)))
    _shape(c,[J(x,y) for x,y in [(3,8),(17,7),(34,12),(51,10),
              (53,16),(49,19),(38,20),(19,26),(8,23),(3,8)]],FUR_PALE,INK,1.8)
    if mouth>.05:
        hpoly([(7,10),(27,4),(49,6),(41,12+12*mouth),(16,17+4*mouth)],'#362d28',None)
        c.poly([J(36,14),J(43,11),J(47,4),J(49,15),J(43,17)],TOOTH,INK,1.1)
    # Upper skull and pointed muzzle. Its short, broken contour makes the
    # cheek read as coarse fur, not a smooth cartoon mouse.
    hshape([(-20,-15),(-10,-30),(6,-31),(17,-23),
            (28,-18),(32,-9),(44,-5),
            (51,-4),(58,-1),(58,5),
            (56,11),(44,12),(35,13),
            (23,17),(15,22),(0,19),
            (-14,18),(-26,4),(-20,-15)],FUR,INK,2.3)
    hshape([(-14,-16),(-4,-27),(10,-27),(18,-20),
            (29,-11),(33,-6),(44,-3),
            (32,-3),(20,-7),(13,-12),
            (4,-16),(-5,-15),(-13,-13)],FUR_LIGHT,None)
    hshape([(6,8),(18,1),(31,-1),(43,1),
            (48,3),(52,5),(51,8),
            (41,10),(30,11),(20,14),
            (12,16),(7,12),(6,7)],FUR_PALE,None)
    # Ear and its root sit in front of the skull, behind the eye and muzzle.
    ear(False)
    for x,y in [(-22,0),(-20,7),(-15,12),(-9,15)]:
        hpoly([(x+3,y-4),(x-4,y),(x+1,y+2),(x-2,y+5),(x+6,y+3)],FUR_DARK,None)

    if dead>.65:
        hline([(9,-10),(14,-7),(19,-10)],INK,2.2)
    elif hurt>.3:
        hline([(8,-12),(14,-8),(20,-12)],INK,2.5)
    else:
        wide = .45+1.4*rear
        hpoly([(6,-15-wide),(24,-8-wide),(20,-4+wide),(10,-5+wide)],'#312f28',INK,1.2)
        hov(16,-9,4.0,2.8+wide*.4,EYE,None)
        hov(17,-9,1.25,2.8,'#211d21',None)
        hov(14,-10,1.0,1.1,'#f8e8c7',None)
        hline([(4,-18-wide),(11,-17-wide),(24,-10.6-wide)],FUR_DARK,4.0)
        hline([(22,-8),(25,-6),(27,-3)],FUR_DARK,1.6)
        hline([(8,-1),(15,0),(19,-2)],FUR_DARK,1.5)
    # Upper incisors lie on the outside edge of the upper jaw. Their base
    # stays fixed when the lower jaw rotates.
    hpoly([(42,8),(49,8),(47,22),(42,21),(40,18)],TOOTH,INK,1.25)
    hpoly([(49,8),(53,7),(52,18),(47,20)],'#b39a60',INK,1.0)
    hline([(45,11),(43,18)],'#a48650',.8)
    if mouth > .35:
        for x,y in [(25,14),(31,13),(36,12)]:
            hpoly([(x-2,y-2),(x+2,y-2),(x+1,y+3),(x-2,y+2)],'#b9a46e',INK,.75)
    hov(54,3,6.4,4.8,SKIN_DARK,INK,1.6,-12)
    hov(55,1,2.5,1.15,SKIN_LIGHT,None)
    # Creased snout and a scar across the cheek.
    hline([(30,-5),(36,-8),(42,-6)],FUR_DARK,1.6)
    hline([(27,1),(32,-2),(38,-1)],FUR_DARK,1.15)
    hline([(2,-4),(6,1),(9,7)],SKIN,1.8)
    hline([(3,-2),(5,1)],FUR_DARK,.9)
    hline([(6,3),(8,5)],FUR_DARK,.9)
    for x,y in [(35,3),(39,5),(33,7)]:
        hov(x,y,.85,.85,FUR_DARK,None)
    # Whiskers follow the muzzle and stay behind the nose tip.
    for pts in [[(37,3),(51,-5),(66,-9)],[(39,5),(54,2),(68,4)],
                [(36,7),(50,10),(63,16)],[(33,8),(44,16),(55,22)]]:
        hline(pts,'#62534b',1.0)
        hline(pts[:2],'#d0b9a1',.65)
    # Viscous saliva follows the mouth rather than a fixed canvas point.
    # Keep the strand short and connected to the lip; it is not a projectile.
    drool = 3.0 + 9.0*mouth + 1.4*math.sin(cyc)
    lip = J(40,18)
    dtip = add(lip,rot((-.9,drool),ha*.3))
    c.line([lip,add(lip,(1.0,2.3)),dtip],SICK,1.65)
    c.oval(dtip,1.6,2.8,SICK,FUR_DARK,.6)
    c.line([add(lip,(.4,1)),add(dtip,(0,-1))],SICK_LIGHT,.65)
    im = c.finish()
    if anim in ('death','death_idle'):
        im = anchored_death(im,GROUND)
    return im


def render(out_dir: str | Path, **opts):
    del opts
    out = build_sheet(target=TARGET_NAME, rows=ROWS, render_fn=_render_frame,
                      out_dir=Path(out_dir), frame_size=FRAME_SIZE, auto_crop=False,
                      actor_metadata=ACTOR_METADATA,
                      body_metrics_fn=lambda w,h: body_metrics_for_box(BODY_BOX,w,h),
                      animation_key_map={name:name for name,_,_ in ROWS},
                      pose_bodies='authored', sits_on_ground=True)
    return [out[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]
