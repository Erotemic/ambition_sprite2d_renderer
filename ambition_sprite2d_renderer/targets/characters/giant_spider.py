"""Giant spider: a dark, hairy hunting spider with eight articulated legs.

The legs plant in alternating groups. The first pair lifts when the spider
notices a target. It draws back and opens its fangs before it strikes.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image

from ._magic_character_art import Canvas, add, sub, mul, mix, unit, perp, rot, bezier, phase, track, anchored_death
from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'giant_spider'
SIDE_FRAME_SIZE = (272, 200)
# Transparent padding keeps reflected poses inside the canvas.
FRAME_SIZE = (336, 200)
SIDE_PAD = 32
GROUND = 168.0
# The core and its ground clearance define the body, not the leg span.
BODY_BOX = (77, 86, 223, 170)
ROWS = [('idle', 12, 100), ('walk', 16, 65), ('run', 16, 45),
        ('turnaround', 3, 73), ('notice', 8, 70), ('windup', 8, 60), ('attack_side', 12, 50),
        ('hit', 8, 55), ('death', 18, 65), ('death_idle', 6, 150)]
LOOPS = {'idle', 'walk', 'run', 'windup', 'death_idle'}
TRAITS = ['enemy', 'fantasy', 'monster', 'spider', 'arachnid']
ACTOR_METADATA = {
    'actor': {'character_id': TARGET_NAME, 'display_name': 'Giant Spider'},
    'body': {'body_plan': 'Multileg', 'body_kind': 'Standard',
             'mass_class': 'Medium', 'locomotion_hint': 'Walk', 'traits': TRAITS},
    'capabilities': {'traversal': {'walk': True}},
    'actions': {'default_preset': 'giant_spider_bite'},
    'visual': {'default_pose': 'idle', 'portrait': {'animation': 'idle', 'frame': 0}},
    'animation_bindings': {
        'default': {'animation': 'idle', 'events': []},
        'locomotion.walk': {'animation': 'walk', 'events': []},
        'locomotion.run': {'animation': 'run', 'events': []},
        'locomotion.turnaround': {'animation': 'turnaround', 'events': []},
        'action.melee.primary': {'animation': 'attack_side', 'events': [
            {'t': 0.0, 'event': 'hitbox_active_start', 'source': 'giant_spider.bite'},
            {'t': .14 / .60, 'event': 'hitbox_active_end', 'source': 'giant_spider.bite'}]},
        'combat.hurt': {'animation': 'hit', 'events': []},
        'combat.death': {'animation': 'death', 'events': []},
    },
    'tags': TRAITS,
    'authoring_description': 'A dark brown hunting spider with eight jointed legs, a mottled abdomen, clustered amber eyes and hooked fangs.',
    'gameplay_description': 'It lifts its front legs when it sees a target. It rears, strikes with its fangs and scuttles away.',
}

INK = '#241c22'
FAR_INK = '#30262b'
LEG = '#61483e'
LEG_LIGHT = '#997560'
LEG_DARK = '#443237'
FAR_LEG = '#49383a'
FAR_LIGHT = '#6a5148'
SHELL = '#59413b'
SHELL_LIGHT = '#88624f'
SHELL_DARK = '#3c2b2b'
HAIR = '#aa8167'
FANG = '#c6a68a'
EYE = '#e7a24e'


def _curve(points):
    out = [points[0]]
    for k in range(1, len(points), 3):
        out.extend(bezier(out[-1], *points[k:k + 3], n=14)[1:])
    return out


def _shape(c, points, color, edge=INK, width=1.9):
    c.poly(_curve(points), color, edge, width)


def _segment(c, a, b, ra, rb, color, light, edge):
    """A tapered leg segment, with a highlight on its own surface."""
    n = perp(unit(sub(b, a)))
    left = [add(a, mul(n, ra)), add(b, mul(n, rb))]
    right = [add(a, mul(n, -ra)), add(b, mul(n, -rb))]
    c.poly(left + right[::-1], color, edge, 1.5)
    c.line([mix(left[0], right[0], .25), mix(left[1], right[1], .25)], light, 1.15)
    # Small bristles stay attached to the segment as it moves.
    for t in (.24, .49, .74):
        r = ra + (rb-ra)*t
        p = mix(a, b, t)
        d = unit(sub(b, a))
        q = add(p, mul(n, r))
        c.line([q, add(add(q, mul(n, 3.0)), mul(d, -2.0))], color, .95)
        q = add(p, mul(n, -r))
        c.line([q, add(add(q, mul(n, -2.6)), mul(d, -2.0))], light, .85)


def _render_side_frame(anim, i, n):
    t = phase(i, n, anim in LOOPS)
    cyc = math.tau*t
    gait = 0.0
    bob = 1.1*math.sin(cyc)
    rear = strike = recoil = curl = 0.0
    gape = .12 + .06*math.sin(cyc)
    alarm = 0.0
    if anim in ('walk', 'run'):
        gait = 1.0 if anim == 'walk' else 1.55
        bob = -1.7*gait*math.cos(2*cyc)
    elif anim == 'notice':
        alarm = track(t, [(0,.48),(.35,1),(1,.8)])
        rear = .54*alarm
        gape = .4*alarm
        bob = 0
    elif anim == 'windup':
        rear = .98 + .02*math.sin(cyc)
        gape = .9 + .08*math.sin(cyc)
        bob = 0
    elif anim == 'attack_side':
        # The active strike comes first. The rest of the row is recovery.
        strike = track(t, [(0,.9),(.12,1),(.20,.87),(.42,.43),(.72,.08),(1,0)])
        gape = track(t, [(0,.95),(.12,.75),(.20,.05),(.35,.2),(1,.12)])
        rear = track(t, [(0,.12),(.2,0),(.75,.08),(1,0)])
        bob = 0
    elif anim == 'hit':
        recoil = track(t, [(0,.75),(.2,1),(.58,.35),(1,0)])
        gape = .7*recoil
        bob = 0
    elif anim in ('death','death_idle'):
        curl = track(t, [(0,0),(.12,.10),(.36,.45),(.77,1),(1,1)]) if anim=='death' else 1.0
        recoil = .65*math.sin(math.pi*min(1,t*2.6)) if anim=='death' else 0
        gape = track(t, [(0,.7),(.28,1),(.65,.4),(1,.05)]) if anim=='death' else .05
        bob = 0
    c = Canvas(SIDE_FRAME_SIZE)
    origin = (134 - 8*rear + 14*strike - 7*recoil, 123 + bob + 19*curl - 5*rear)
    pitch = -18*rear + 10*strike - 9*recoil + 10*curl

    def B(x,y):
        return add(origin, rot((x,y), pitch))
    def oval(x,y,rx,ry,color,edge=INK,w=1.7,angle=0):
        c.oval(B(x,y),rx,ry,color,edge,w,pitch+angle)
    def shape(pts,color,edge=INK,w=1.9):
        _shape(c,[B(x,y) for x,y in pts],color,edge,w)
    def line(pts,color,w=1.4):
        c.line([B(x,y) for x,y in pts],color,w)

    # A right-facing three-quarter projection. Each leg has its own coxa,
    # femur, knee, tibia, and tarsus. Keep the face clear of the near front
    # femur: it first extends out of the lower carapace before rising.
    # Far-side knees and feet have a different silhouette, not a copy of
    # the near-side chain displaced by a few pixels.
    def leg(k, near):
        roots = ((24,12),(9,15),(-3,14),(-15,9)) if near else ((23,-3),(10,-5),(-2,-4),(-13,-2))
        coxae = ((39,16),(8,20),(-13,18),(-27,12)) if near else ((34,-12),(16,-14),(-12,-14),(-25,-11))
        knees = ((66,-25),(-8,-35),(-37,-34),(-66,-20)) if near else ((50,-43),(17,-49),(-26,-45),(-58,-35))
        feet = (245,151,100,38) if near else (221,184,77,29)
        gy = GROUND if near else GROUND-13
        root, coxa = B(*roots[k]), B(*coxae[k])
        fx, fy = feet[k], gy
        if gait:
            p = cyc + (0 if (k % 2 == 0)==near else math.pi)
            fx += 11*gait*math.cos(p)
            fy -= 12*gait*max(0,math.sin(p))
        if k == 0:
            fx += 4*rear + 8*strike
            fy -= (63 if near else 49)*rear + 10*strike
        elif k == 1:
            fx += 5*rear + 5*strike
            fy -= (21 if near else 15)*rear
        fx += (k-1.5)*3*recoil
        kx,ky = knees[k]
        knee = B(kx + .31*(fx-feet[k]), ky - .20*(gy-fy))
        if rear and k == 0:
            knee = mix(knee,B(55 if near else 36,-43 if near else -54),rear)
        if strike and k == 0:
            knee = mix(knee,B(72 if near else 53,-15 if near else -21),strike)
        foot = (fx,fy)
        if curl:
            # The rear legs fold backwards; front legs curl towards the
            # underside. Keep the two folded silhouettes staggered in depth.
            fold_coxae = ((32,12),(10,20),(-14,18),(-29,9)) if near else ((29,-8),(9,-15),(-13,-14),(-27,-10))
            fold_knees = ((48,-15),(-3,-25),(-29,-23),(-48,-10)) if near else ((38,-23),(21,-34),(-19,-32),(-43,-22))
            fold_feet = ((24,17),(4,25),(-16,23),(-33,14)) if near else ((22,5),(7,12),(-12,11),(-31,4))
            coxa = mix(coxa,B(*fold_coxae[k]),curl)
            knee = mix(knee,B(*fold_knees[k]),curl)
            foot = mix(foot,B(*fold_feet[k]),curl)
            foot = (foot[0],min(gy,foot[1]))
        ankle = mix(knee,foot,.80)
        ankle = add(ankle, mul(perp(unit(sub(foot,knee))), 3.3 if k<2 else -3.3))
        col, light, edge = (LEG,LEG_LIGHT,INK) if near else (FAR_LEG,FAR_LIGHT,FAR_INK)
        # Paint each leg as a complete chain. The coxa caps its root and
        # the joint caps cover seams, rather than layering all femurs over
        # all tibias (which produces impossible crossings).
        _segment(c, ankle, foot, 2.1 if near else 1.8, .7, LEG_DARK if near else FAR_LEG, light, edge)
        _segment(c, knee, ankle, 3.9 if near else 3.0, 2.2 if near else 1.8, col, light, edge)
        _segment(c, coxa,knee,5.2 if near else 3.8,3.9 if near else 3.0,col,light,edge)
        c.disk(knee,3.7 if near else 2.9,LEG_DARK if near else FAR_LEG,edge,1.1)
        c.line([mix(coxa,knee,.92),mix(knee,ankle,.10)],light,1.05 if near else .8)
        _segment(c, root,coxa,5.2 if near else 3.7,5.0 if near else 3.8,col,light,edge)
        c.disk(coxa,4.2 if near else 3.1,col,None)
        c.line([mix(root,coxa,.48),mix(coxa,knee,.12)],light,1.1 if near else .75)

    for k in (3,2,1,0):
        leg(k,False)

    # Pedicel and abdomen. The belly is rounded; the upper plate has
    # a muted mottled pattern. Hair follows the silhouette of the abdomen.
    oval(-18,0,14,10,SHELL_DARK)
    abdomen = [(-17,-10),(-19,-31),(-43,-39),(-65,-34),(-87,-30),(-94,-12),(-88,7),
               (-83,25),(-58,31),(-37,23),(-25,20),(-15,10),(-17,-10)]
    shape(abdomen,SHELL,INK,2.5)
    shape([(-87,-7),(-88,-26),(-64,-34),(-42,-29),(-28,-24),(-25,-18),(-24,-13),
           (-52,-23),(-69,-18),(-78,-6),(-83,-1),(-86,-3),(-87,-7)],SHELL_LIGHT,None)
    shape([(-88,4),(-79,13),(-67,17),(-51,17),(-36,16),(-26,8),(-20,3),
           (-26,22),(-52,30),(-67,24),(-80,21),(-87,15),(-88,4)],SHELL_DARK,None)
    for x,y in [(-73,-21),(-56,-25),(-39,-19),(-70,5),(-50,7),(-31,1)]:
        oval(x,y,7,3.0,'#6b493d',None,angle=-12)
    for j in range(18):
        a = math.radians(85+15*j)
        p = (-54+34*math.cos(a),-3+26*math.sin(a))
        q = add(p,(4.3*math.cos(a),4.0*math.sin(a)))
        line([p,q],HAIR if j>6 else LEG_DARK,1.0)
    for x,y in [(-82,-12),(-73,-18),(-67,-11),(-59,-20),(-48,-14),(-39,-9),(-76,1),(-61,8),(-44,8)]:
        line([(x,y),(x+4,y-2)],'#ad8263',.85)
    # Spinnerets sit at the rear of the abdomen.
    oval(-86,11,5,3,SHELL_DARK,INK,1.1,angle=-22)

    # The front body has a raised carapace and a low face, rather than a
    # separate humanoid head. Draw the near legs over the lower body plate.
    shape([(-23,2),(-22,-20),(-7,-28),(17,-22),(29,-19),(42,-6),(41,7),
           (39,22),(20,24),(1,20),(-14,18),(-23,13),(-23,2)],SHELL,INK,2.4)
    shape([(-17,-5),(-15,-18),(-4,-22),(13,-19),(24,-17),(32,-11),(33,-6),
           (15,-13),(1,-12),(-7,-4),(-12,0),(-16,-1),(-17,-5)],SHELL_LIGHT,None)
    line([(-18,6),(-8,12),(8,15),(26,13)],SHELL_DARK,2.2)
    # Eyes occupy their own face plate, outside the near leg chains. A pair of larger forward eyes and
    # six small eyes give the head the anatomy of a hunting spider.
    shape([(13,-12),(20,-18),(31,-15),(36,-8),(40,-3),(37,2),(32,4),
           (22,4),(13,0),(13,-12)],'#36282a',None)
    eyes = [(22,-7,4.8,4.2),(34,-5,4.2,3.8),(15,-14,2.6,2.3),
            (23,-16,2.7,2.4),(31,-14,2.6,2.4),(37,-11,2.0,2.1),
            (14,1,1.9,1.8),(29,3,1.8,1.6)]
    for x,y,rx,ry in eyes:
        oval(x,y,rx,ry,'#211a21',INK,1.0)
        if curl<.72:
            color = EYE if curl<.32 and recoil<.6 else '#99623c'
            oval(x+.5,y,rx*.72,ry*.73,color,None)
            if rx>3:
                oval(x+1.1,y+.25,rx*.28,ry*.61,'#35222a',None)
                oval(x-.8,y-1.1,rx*.20,ry*.21,'#f7d19c',None)
            else:
                oval(x-.5,y-.6,rx*.22,ry*.23,'#f3c18a',None)
    # The two chelicerae and their curved fangs move as distinct parts.
    def fang(near):
        x,y = (35,8) if near else (41,3)
        spread = gape*(11 if near else 7)
        s = 1 if near else -1
        a = (x,y)
        b = (x+7+spread,y+5+s*spread*.24)
        d = (x+9+spread,y+13+s*spread*.7)
        e = (x+3+spread,y+17+s*spread*.8)
        line([a,b],INK,9 if near else 7)
        line([a,b],SHELL_DARK if near else FAR_LEG,6 if near else 4.6)
        shape([b,(b[0]+4,b[1]),(d[0]+4,d[1]-2),d,(d[0]-1,d[1]+3),(e[0]+2,e[1]+1),e,
               (e[0]+1,e[1]-4),(b[0]-1,b[1]+4),b],FANG if near else '#8f7464',INK,1.3)
    fang(False)
    # Pedipalps frame the fangs. They are short, not additional walking legs.
    oval(27,11,5.2,6.2,LEG_DARK,INK,1.1,angle=-30)
    fang(True)
    # Foreground legs overlay the carapace, abdomen, and face if their
    # projected geometry actually crosses them. Rear legs remain behind.
    for k in (3,2,1,0):
        leg(k,True)
    im = c.finish()
    if anim in ('death', 'death_idle'):
        im = anchored_death(im, GROUND + 1)
    return im


def _front_frame():
    """Head-on elevated view. Eight separately projected articulated legs."""
    c=Canvas(FRAME_SIZE)
    cx=(BODY_BOX[0]+BODY_BOX[2]-1)/2
    def P(x,y): return (cx+x,y)
    def pts(seq,s=1): return [P(s*x,y) for x,y in seq]
    def shape(seq,col,edge=INK,w=1.9,s=1): _shape(c,pts(seq,s),col,edge,w)
    def oval(x,y,rx,ry,col,edge=INK,w=1.7,angle=0): c.oval(P(x,y),rx,ry,col,edge,w,angle)
    def line(seq,col=INK,w=1.4,s=1): c.line(pts(seq,s),col,w)
    # Each successive pair is nearer the viewer. The knees fan out along
    # different rays; the four tarsi on each side land on separate rows.
    # The front pair stays outside the eye plate and the two fangs.
    legs=[((17,106),(29,103),(47,68),(60,137)),
          ((23,114),(37,110),(79,69),(94,145)),
          ((26,122),(42,122),(104,87),(119,158)),
          ((27,133),(43,138),(66,120),(82,168))]
    def leg(k,s):
        a,b,d,e=pts(legs[k],s)
        f=add(mix(d,e,.80),mul(perp(unit(sub(e,d))),s*2.5))
        near=k>=2
        col,light,edge=(LEG,LEG_LIGHT,INK) if near else (FAR_LEG,FAR_LIGHT,FAR_INK)
        r=1 if near else .83
        _segment(c,f,e,2.1*r,.7,col,light,edge)
        _segment(c,d,f,3.9*r,2.2*r,col,light,edge)
        _segment(c,b,d,5.2*r,3.9*r,col,light,edge)
        c.disk(d,3.7*r,LEG_DARK if near else FAR_LEG,edge,1.1)
        c.line([mix(b,d,.92),mix(d,f,.10)],light,1.05*r)
        _segment(c,a,b,5.2*r,5*r,col,light,edge)
        c.disk(b,4.2*r,col,None)
        c.line([mix(a,b,.48),mix(b,d,.12)],light,1.1*r)
    for k in (0,1):
        for s in (-1,1): leg(k,s)
    # Abdomen is seen behind and above the cephalothorax. The pedicel
    # disappears behind the front body, not between the eyes.
    oval(0,109,13,10,SHELL_DARK)
    shape([(0,75),(22,73),(36,84),(38,100),(41,116),(27,133),(0,136),
           (-27,133),(-41,116),(-38,100),(-36,84),(-22,73),(0,75)],SHELL,INK,2.5)
    shape([(-33,98),(-30,82),(-13,78),(0,79),(13,77),(30,83),(33,98),
           (13,91),(-12,91),(-33,98)],SHELL_LIGHT,None)
    shape([(-35,111),(-26,121),(-12,124),(0,124),(12,124),(26,121),(35,111),
           (31,132),(12,135),(0,135),(-12,135),(-31,132),(-35,111)],SHELL_DARK,None)
    for x,y,ang in [(-22,87,24),(-7,84,-7),(13,87,-20),(27,95,38),(-26,103,16),(8,100,-16)]:
        oval(x,y,6.5,3,'#6b493d',None,angle=ang)
    for j in range(19):
        a=math.radians(188+9*j)
        x,y=37*math.cos(a),103+27*math.sin(a)
        line([(x,y),(x+4*math.cos(a),y+4*math.sin(a))],HAIR,1)
    for x,y in [(-29,88),(-17,82),(-5,81),(10,84),(25,90),(-30,101),(30,104)]:
        line([(x,y),(x+2,y-3)],'#ad8263',.85)
    # Cephalothorax, viewed head-on, with a raised carapace and broad
    # low eye plate. The eye pattern preserves the two dominant eyes.
    shape([(0,100),(20,100),(34,111),(35,125),(37,141),(22,152),(0,152),
           (-22,152),(-37,141),(-35,125),(-34,111),(-20,100),(0,100)],SHELL,INK,2.4)
    shape([(-29,118),(-26,107),(-11,104),(0,105),(11,104),(26,107),(29,118),
           (16,113),(-16,113),(-29,118)],SHELL_LIGHT,None)
    shape([(-23,121),(-20,112),(-8,114),(0,114),(8,114),(20,112),(23,121),
           (26,134),(13,142),(0,141),(-13,142),(-26,134),(-23,121)],'#36282a',None)
    for s in (-1,1):
        for x,y,rx,ry in [(9,126,5.1,4.8),(19,128,3.2,3.1),(7,117,2.7,2.4),(18,117,2.5,2.2)]:
            oval(s*x,y,rx,ry,'#211a21',INK,1)
            oval(s*x,y,rx*.74,ry*.74,EYE,None)
            if rx>3:
                oval(s*x,y+.25,rx*.29,ry*.62,'#35222a',None)
            oval(s*x-.9,y-1.05,rx*.20,ry*.21,'#f7d19c',None)
    # Each chelicera and its fang hangs below the eyes. Small palps are
    # separate from (and visibly shorter than) the eight walking legs.
    for s in (-1,1):
        oval(s*22,143,5.2,6.2,LEG_DARK,INK,1.1,angle=s*25)
        shape([(6,140),(8,136),(14,137),(16,142),(17,147),(13,152),(9,151),
               (6,149),(4,144),(6,140)],SHELL_DARK,INK,1.5,s)
        shape([(9,148),(13,147),(16,151),(15,155),(14,161),(10,164),(5,164),
               (9,160),(11,154),(9,148)],FANG,INK,1.3,s)
        line([(12,150),(13,154),(10,160)],'#e0bfa4',.9,s)
    # Foreground leg chains overlap the lower side of the carapace only.
    for k in (2,3):
        for s in (-1,1): leg(k,s)
    return c.finish()


def _render_frame(anim, i, n):
    if anim == 'turnaround':
        assert n == 3
        if i == 1:
            return _front_frame()
        im = _render_frame('idle', 0, 12)
        if i == 2:
            return im
        # The runtime uses the new facing. Mirror the old-facing endpoint
        # about the authored body anchor, never about the canvas center.
        out = Image.new('RGBA', FRAME_SIZE)
        out.paste(im.transpose(Image.Transpose.FLIP_LEFT_RIGHT),
                  (BODY_BOX[0]+BODY_BOX[2]-im.width, 0))
        return out
    im = _render_side_frame(anim, i, n)
    out = Image.new('RGBA', FRAME_SIZE)
    out.paste(im, (SIDE_PAD, 0))
    return out


def render(out_dir: str | Path, **opts):
    del opts
    out = build_sheet(
        target=TARGET_NAME, rows=ROWS, render_fn=_render_frame,
        out_dir=Path(out_dir), frame_size=FRAME_SIZE, auto_crop=False,
        actor_metadata=ACTOR_METADATA,
        body_metrics_fn=lambda w,h: body_metrics_for_box(BODY_BOX,w,h),
        animation_key_map={name:name for name,_,_ in ROWS},
        pose_bodies='authored', sits_on_ground=True,
    )
    return [out[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]
