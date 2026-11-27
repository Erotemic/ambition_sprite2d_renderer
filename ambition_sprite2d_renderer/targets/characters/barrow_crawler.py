"""Barrow Crawler: a burial corpse that pulls itself along on its arms.

The hips stay low. Alternate the two hands during travel. Raise the chest
before the lunge, then lower the face to the floor during recovery.
The lunge moves the body in the game; the art shows the change in posture.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import math
from pathlib import Path

from ._clockwork_enemy_art import Canvas, add, sub, mul, mix, phase, rot, track
from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'barrow_crawler'
DISPLAY_NAME = 'Barrow Crawler'
FRAME_SIZE = (280, 164)
CX, GROUND = 128., 138.
ROWS = [
    ('idle', 8, 150), ('walk', 12, 110), ('run', 12, 90),
    ('notice', 8, 90), ('windup', 8, 100), ('attack_side', 18, 69),
    ('hit', 6, 85), ('death', 12, 100), ('death_idle', 6, 200),
]
LOOPS = {'idle', 'walk', 'run', 'windup', 'death_idle'}
TRAITS = ['enemy', 'undead', 'zombie', 'barrow', 'minion', 'combatant', 'crawler', 'slow']
ACTOR_METADATA = {
    'actor': {'character_id': TARGET_NAME, 'display_name': DISPLAY_NAME},
    'body': {'body_plan': 'HumanoidBiped', 'body_kind': 'Standard',
             'mass_class': 'Medium', 'locomotion_hint': 'Crawl', 'traits': TRAITS},
    'capabilities': {'traversal': {'walk': True, 'crawl': True}},
    'brain': {'default_preset': 'melee_brute_striker'},
    'actions': {'default_preset': 'barrow_crawler_lunge'},
    'visual': {'default_pose': 'idle', 'portrait': {'animation': 'idle', 'frame': 0}},
    'animation_bindings': {
        'default': {'animation': 'idle', 'events': []},
        'locomotion.walk': {'animation': 'walk', 'events': []},
        'locomotion.run': {'animation': 'run', 'events': []},
        'action.melee.primary': {'animation': 'attack_side', 'events': [
            {'t': 0.0, 'event': 'hitbox_active_start', 'source': 'barrow_crawler.lunge'},
            {'t': 0.14 / 1.24, 'event': 'hitbox_active_end', 'source': 'barrow_crawler.lunge'},
        ]},
        'combat.hurt': {'animation': 'hit', 'events': []},
        'combat.death': {'animation': 'death', 'events': []},
    },
    'tags': TRAITS,
    'authoring_description': 'A legless burial corpse in torn linen. It has long arms, a slack jaw, and a shroud that trails behind its hips.',
    'gameplay_description': 'A low enemy that waits for a target, raises one arm, lunges along the floor, and lies exposed during recovery.',
}

# Match the colors of the burial cloth and dead skin of the Barrow Shambler.
INK = '#2e292e'
SKIN, SKIN_L, SKIN_D, DEEP = '#85988b', '#a9b3a0', '#51675e', '#394a46'
BONE, EYE, MOUTH = '#d2c8a7', '#b9eac7', '#33292c'
LINEN, LINEN_L, LINEN_D, CLOTH_D = '#b1a07f', '#dbcb9f', '#78684f', '#534b40'


@dataclass(frozen=True)
class Pose:
    pitch: float = -17.
    shift: float = 0.
    near_x: float = 58.
    near_y: float = -5.
    far_x: float = 40.
    far_y: float = -5.
    jaw: float = 2.
    rag: float = 0.
    head_tilt: float = -4.
    eyes: float = 1.
    near_angle: float = 0.
    far_angle: float = 0.


LOW = Pose()
REARED = Pose(pitch=-42, shift=-5, near_x=-29, near_y=-100, far_x=16, far_y=-5,
              jaw=5, rag=-3, head_tilt=-8, near_angle=-118)
LUNGED = Pose(pitch=-11, shift=10, near_x=79, near_y=-7, far_x=65, far_y=-5,
              jaw=6, rag=3, head_tilt=9)
SPENT = Pose(pitch=3, shift=7, near_x=65, near_y=-5, far_x=52, far_y=-5,
             jaw=3, head_tilt=56, eyes=0.25)
DEAD = replace(SPENT, shift=0, head_tilt=67, eyes=0, jaw=4)


def _blend(a, b, t):
    return Pose(**{name: getattr(a, name) + (getattr(b, name)-getattr(a, name))*t
                   for name in Pose.__dataclass_fields__})


def _keys(t, keys):
    for (ta, a), (tb, b) in zip(keys, keys[1:]):
        if t <= tb:
            return _blend(a, b, track(t, [(ta, 0.), (tb, 1.)]))
    return keys[-1][1]


def pose(anim, i, n):
    t = phase(i, n, anim in LOOPS)
    p = math.tau*t
    s, c = math.sin(p), math.cos(p)
    if anim == 'idle':
        return replace(LOW, pitch=-17+1.7*s, jaw=2+.7*s, rag=1.8*s)
    if anim in ('walk', 'run'):
        # Face +x: reach forward with a lifted hand, then plant and pull
        # backward. Keep the torso and trailing cloth phase unchanged.
        reach = 19 if anim == 'walk' else 23
        near_lift, far_lift = max(0, -s), max(0, s)
        return replace(LOW, pitch=-17-3*abs(s), shift=2*c,
                       near_x=46+reach*c, near_y=-5-13*near_lift,
                       far_x=40-reach*c, far_y=-5-11*far_lift,
                       near_angle=-22*near_lift, far_angle=-18*far_lift, rag=3*s)
    if anim == 'notice':
        up = replace(REARED, near_x=36, near_y=-5, near_angle=0, pitch=-36)
        return _keys(t, [(0,LOW),(.45,up),(1,up)])
    if anim == 'windup':
        return replace(REARED, near_x=-29+1.8*s, near_y=-100+1.5*c, jaw=5+.6*s)
    if anim == 'attack_side':
        # The engine pins windup separately. This row is strike + recovery.
        return _keys(t, [(0,REARED),(.055,LUNGED),(.115,LUNGED),(.24,SPENT),(.73,SPENT),(1,LOW)])
    if anim == 'hit':
        hit = replace(LOW, pitch=-32, shift=-6, near_x=33, near_y=-23,
                      near_angle=-28, head_tilt=-24, jaw=5, eyes=.55)
        return _keys(t, [(0,LOW),(.25,hit),(.55,hit),(1,LOW)])
    if anim == 'death':
        up = replace(LOW, pitch=-29, near_x=38, jaw=5, eyes=.5)
        return _keys(t, [(0,LOW),(.22,up),(.65,DEAD),(1,DEAD)])
    if anim == 'death_idle':
        return DEAD
    raise ValueError(anim)


def _elbow(shoulder, hand):
    """Bend two arm segments toward the rear when the hand is on the floor."""
    v=sub(hand,shoulder); length=max(.01,math.hypot(*v))
    u=mul(v,1/length)
    # Place the elbow to the rear of the wrist path.
    mid=mul(v,.47)
    height=math.sqrt(max(0.,29**2-min(29.,length*.47)**2))
    n=(u[1],-u[0])
    return add(shoulder,add(mid,mul(n,height)))


def _render_frame(anim, i, n):
    q=pose(anim,i,n); d=Canvas(FRAME_SIZE)
    hip=(CX-43+q.shift,GROUND-17)
    def B(x,y): return add(hip,rot((x,y),q.pitch))
    def poly(pts,c,edge=INK,w=1.5): d.poly([B(*p) for p in pts],c,edge,w)
    def line(pts,c,w=1.4): d.line([B(*p) for p in pts],c,w)

    # The rear of the shroud covers the stumps. Its torn ends drag on stone.
    back=B(-8,-9)
    d.poly([back,B(14,-16),(hip[0]-18,GROUND-4),(hip[0]-37,GROUND-3),
            (hip[0]-29+q.rag,GROUND-8),(hip[0]-49,GROUND-5),(hip[0]-40,GROUND-13),
            (hip[0]-24,GROUND-18)],LINEN_D,INK,1.6)
    d.poly([B(4,-12),B(12,-6),(hip[0]-20,GROUND-6),(hip[0]-32,GROUND-8),
            (hip[0]-19,GROUND-14)],LINEN, None)
    d.line([B(2,-10),(hip[0]-18,GROUND-11),(hip[0]-35,GROUND-6)],LINEN_L,1.5)
    # Two linen-covered remnants. No blood or exposed gore.
    for j,dy in enumerate((-1,4)):
        a=B(4,dy); b=(hip[0]-20+j*8,GROUND-8+j*3)
        d.tube(a,b,6.3,LINEN_D if j==0 else LINEN,LINEN if j==0 else LINEN_L,LINEN_D)
        d.poly([add(b,(-8,-5)),add(b,(-12,-1)),add(b,(-8,1)),add(b,(-11,4)),add(b,(1,5)),add(b,(3,-4))],CLOTH_D,INK,1.1)

    def arm(near):
        shoulder=B(42,-4 if near else -10)
        hand=(CX+(q.near_x if near else q.far_x),GROUND+(q.near_y if near else q.far_y))
        elbow=_elbow(shoulder,hand)
        # Do not put the elbow through the ground.
        elbow=(elbow[0],min(GROUND-7,elbow[1]))
        c=SKIN if near else SKIN_D; l=SKIN_L if near else SKIN
        d.tube(shoulder,elbow,7.6,c,l,DEEP)
        d.tube(shoulder,mix(shoulder,elbow,.45),8.5,LINEN if near else LINEN_D,LINEN_L if near else LINEN)
        d.disk(elbow,6.4,c,INK,1.3)
        d.tube(elbow,hand,5.6,c,l,DEEP)
        if near:
            for a in (.15,.32):
                d.tube(mix(elbow,hand,a),mix(elbow,hand,a+.10),6.6,LINEN,LINEN_L,LINEN_D)
        ang=q.near_angle if near else q.far_angle
        def H(x,y): return add(hand,rot((x,y),ang))
        d.oval(hand,7.4,4.8,c,INK,1.2,ang)
        for j,L in enumerate((10,15,14,10)):
            y=-4+j*2.5
            pts=[H(4,y),H(L*.7,y),H(L,y+1)]
            d.line(pts,INK,3.4); d.line(pts,l if near else c,2.)
            d.line([H(L-2,y+.7),H(L,y+1)],BONE,1.2)
        d.line([H(-1,3),H(4,5)],INK,3.5); d.line([H(-1,3),H(4,5)],c,2.)

    arm(False)
    # Long, narrow body; the diagonal bands are burial linen, not a uniform.
    poly([(-8,-10),(9,-16),(27,-18),(44,-16),(52,-8),(50,4),(38,12),
          (23,9),(15,14),(9,10),(2,14),(-5,8)],LINEN)
    poly([(-4,4),(12,6),(24,3),(39,6),(50,0),(43,10),(26,9),(15,14),(2,14)],LINEN_D,None)
    poly([(21,-13),(41,-13),(45,-5),(36,1),(24,-3),(19,-7)],SKIN_D)
    for j in range(3): line([(25+5*j,-10),(25+5*j,-4)],BONE,2.1)
    for x in (4,13,22):
        poly([(x,-16),(x+5,-17),(x+19,5),(x+14,8),(x+9,4)],LINEN_L,LINEN_D,1.)
    line([(5,-15),(2,-4),(7,9)],LINEN_D,2.2)
    line([(7,-15),(4,-4),(9,8)],LINEN_L,1.0)
    # A knot and an unraveling shoulder wrap.
    poly([(35,-16),(44,-18),(50,-9),(43,-8)],LINEN_L,LINEN_D,1.1)
    line([(39,-15),(45,-9)],LINEN_D,1.)
    # Neck and raised skull; its angle is independent of the body pitch.
    neck=B(49,-8); head=B(65,-18)
    # Keep the face above ground while it drops forward in recovery.
    head=(head[0],min(head[1],GROUND-23))
    d.tube(neck,head,9,SKIN_D,SKIN,DEEP)
    a=q.head_tilt
    def H(x,y): return add(head,rot((x,y),a))
    def hp(pts,c,edge=INK,w=1.4):d.poly([H(*p) for p in pts],c,edge,w)
    def hl(pts,c,w=1.4):d.line([H(*p) for p in pts],c,w)
    def ho(x,y,rx,ry,c,edge=INK,w=1.3):d.oval(H(x,y),rx,ry,c,edge,w,a)
    ho(0,-2,20,21,SKIN)
    hp([(-15,-15),(-19,-4),(-14,9),(-5,16),(6,16),(15,11),(18,2),(17,-11),(10,-18)],SKIN)
    hp([(-17,-10),(-15,4),(-7,8),(-4,14),(-12,13),(-19,2)],SKIN_D,None)
    hp([(-9,-14),(-2,-19),(10,-16),(8,-13),(-5,-12)],SKIN_L,None)
    hp([(-6,-8),(4,-11),(11,-7),(8,0),(-2,1),(-7,-3)],DEEP)
    hp([(13,-9),(17,-7),(19,-3),(14,0),(11,-3)],DEEP)
    if q.eyes>.05:
        ho(2,-5,3.4,3.2*q.eyes,EYE,None)
        ho(15,-5,2.2,2.0*q.eyes,EYE,None)
    hp([(9,-5),(15,2),(12,5),(7,2)],SKIN_L,SKIN_D,1.1)
    hp([(-3,5),(7,3),(17,6),(16,11+q.jaw),(8,14+q.jaw),(-1,11+q.jaw)],MOUTH)
    for x in (1,5,9,13):hp([(x,5),(x+3,5),(x+3,10),(x,9)],BONE,None)
    hl([(-1,11+q.jaw),(8,14+q.jaw),(16,11+q.jaw)],SKIN,3.4)
    # A partially unwound bandage and a few strands of hair.
    hp([(-17,-17),(-15,-24),(-11,-20),(-5,-25),(-1,-22),(5,-24),(10,-19),(-6,-16)],CLOTH_D)
    hp([(-17,-18),(-9,-22),(7,-21),(18,-15),(16,-10),(4,-14),(-17,-12)],LINEN,LINEN_D,1.)
    hl([(-14,-17),(-6,-19),(7,-18),(14,-14)],LINEN_L,1.8)
    hl([(-15,-14),(-22,-8),(-24,0)],LINEN_D,3.)
    arm(True)
    return d.finish()


def _body_metrics(fw, fh):
    # The low torso and head form the body. Reaching hands and loose cloth do not.
    return body_metrics_for_box((CX-73, 59, CX+40, GROUND+2), fw, fh)


def render(out_dir: str | Path, **opts):
    out_dir=Path(out_dir); out_dir.mkdir(parents=True,exist_ok=True)
    outputs=build_sheet(target=TARGET_NAME, rows=ROWS, render_fn=_render_frame,
                        out_dir=out_dir, frame_size=FRAME_SIZE, auto_crop=False,
                        actor_metadata=ACTOR_METADATA, body_metrics_fn=_body_metrics,
                        animation_key_map={a:a for a,_,_ in ROWS}, sits_on_ground=True)
    return [outputs[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]
