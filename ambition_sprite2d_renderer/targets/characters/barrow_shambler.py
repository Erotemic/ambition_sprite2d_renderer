"""Barrow Shambler: a weak, unarmored corpse in rotted burial linen.

Asymmetric limbs, a dragged foot and a slow open-handed swipe. The wight
is a soldier; this is simply one of the valley's long-dead inhabitants.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

from ._clockwork_enemy_art import Canvas, add, mix, phase, rot, track, anchored_death
from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'barrow_shambler'
DISPLAY_NAME = 'Barrow Shambler'
FRAME_SIZE = (264, 224)
CX, GROUND = 120., 200.
WINDUP_S, ACTIVE_S, RECOVER_S = .48, .12, .55
ROWS = [
    ('idle', 12, 120), ('walk', 12, 110), ('run', 12, 85),
    ('notice', 8, 90), ('windup', 8, 60), ('attack_side', 23, 50),
    ('hit', 5, 80), ('death', 14, 90),
]
LOOPS = {'idle', 'walk', 'run', 'windup'}
TRAITS = ['enemy', 'undead', 'zombie', 'barrow', 'minion', 'combatant']
ACTOR_METADATA = {
    'actor': {'character_id': TARGET_NAME, 'display_name': DISPLAY_NAME},
    'body': {'body_plan': 'HumanoidBiped', 'body_kind': 'Standard',
             'mass_class': 'Medium', 'locomotion_hint': 'Walk', 'traits': TRAITS},
    'brain': {'default_preset': 'melee_brute_striker'},
    'actions': {'default_preset': 'barrow_shambler_swipe'},
    'visual': {'default_pose': 'idle', 'portrait': {'animation': 'idle', 'frame': 0}},
    'animation_bindings': {
        'default': {'animation': 'idle', 'events': []},
        'locomotion.walk': {'animation': 'walk', 'events': []},
        'locomotion.run': {'animation': 'run', 'events': []},
        'action.melee.primary': {'animation': 'attack_side', 'events': [
            {'t': WINDUP_S / (WINDUP_S + ACTIVE_S + RECOVER_S),
             'event': 'hitbox_active_start', 'source': 'barrow_shambler.swipe'},
            {'t': (WINDUP_S + ACTIVE_S) / (WINDUP_S + ACTIVE_S + RECOVER_S),
             'event': 'hitbox_active_end', 'source': 'barrow_shambler.swipe'},
        ]},
        'combat.hurt': {'animation': 'hit', 'events': []},
        'combat.death': {'animation': 'death', 'events': []},
    },
    'tags': TRAITS,
    'authoring_description': 'A desiccated valley corpse in torn burial linen, with a slack jaw, one bare leg, and an unraveling sleeve.',
    'gameplay_description': 'A fragile, slow, unarmed barrow minion with a telegraphed short swipe. No passive contact damage.',
}

INK = '#2e292e'
SKIN = '#85988b'
SKIN_L = '#a9b3a0'
SKIN_D = '#51675e'
DEEP = '#394a46'
BONE = '#d2c8a7'
LINEN = '#b1a07f'
LINEN_L = '#dbcb9f'
LINEN_D = '#78684f'
CLOTH = '#716451'
CLOTH_D = '#534b40'
HAIR = '#59554b'
EYE = '#b9eac7'
MOUTH = '#33292c'


@dataclass(frozen=True)
class Pose:
    lean: float = 14.
    bob: float = 0.
    stride: float = 0.
    ph: float = 0.
    hand_x: float = 47.
    hand_y: float = -90.
    elbow_x: float = 8.
    elbow_y: float = -80.
    far_x: float = 24.
    far_y: float = -70.
    jaw: float = 1.
    rag: float = 0.
    recoil: float = 0.
    fall: float = 0.


def pose(anim, i, n):
    t = phase(i, n, anim in LOOPS)
    p = math.tau * t
    if anim == 'idle':
        return Pose(lean=14+2*math.sin(p), bob=1.5*math.sin(p), hand_y=-90+3*math.sin(p), jaw=1+.5*math.sin(p), rag=2*math.sin(p))
    if anim in ('walk', 'run'):
        st = .68 if anim == 'walk' else 1.
        return Pose(lean=17+3*math.sin(p), bob=-2*abs(math.sin(p)), stride=st, ph=p,
                    hand_x=47+5*math.sin(p), hand_y=-88+5*math.sin(p),
                    far_y=-70-4*math.sin(p), rag=5*math.sin(p))
    if anim == 'notice':
        s=math.sin(math.pi*t)
        return Pose(lean=14-10*s, bob=-3*s, hand_y=-90-13*s, jaw=1+4*s)
    if anim == 'windup':
        return Pose(lean=-8, bob=-3, hand_x=0, hand_y=-126+1.3*math.sin(p),
                    elbow_x=-33, elbow_y=-103, far_x=33, far_y=-101, jaw=4, rag=-5)
    if anim == 'attack_side':
        a=WINDUP_S/(WINDUP_S+ACTIVE_S+RECOVER_S)
        b=(WINDUP_S+ACTIVE_S)/(WINDUP_S+ACTIVE_S+RECOVER_S)
        peak=a+.038
        def k(keys): return track(t,keys)
        return Pose(lean=k([(0,-8),(a,-8),(peak,30),(b,30),(.75,23),(1,14)]),
                    bob=k([(0,-3),(a,-3),(peak,3),(b,3),(1,0)]),
                    hand_x=k([(0,0),(a,0),(peak,83),(b,80),(.76,60),(1,47)]),
                    hand_y=k([(0,-126),(a,-126),(peak,-93),(b,-84),(1,-90)]),
                    elbow_x=k([(0,-33),(a,-33),(peak,39),(b,38),(1,8)]),
                    elbow_y=k([(0,-103),(a,-103),(peak,-97),(b,-89),(1,-80)]),
                    far_x=k([(0,33),(a,33),(peak,52),(b,48),(1,24)]),
                    far_y=k([(0,-101),(a,-101),(peak,-85),(b,-79),(1,-70)]),
                    jaw=k([(0,4),(a,4),(peak,6),(b,6),(1,1)]),
                    rag=k([(0,-5),(a,-5),(peak,10),(b,10),(1,0)]))
    if anim == 'hit':
        s=math.sin(math.pi*t)
        return Pose(lean=14-25*s, bob=-5*s, recoil=s, hand_x=47-22*s, hand_y=-90-13*s, jaw=1+3*s)
    if anim == 'death':
        f=track(t,[(0,0),(.13,0),(.86,1),(1,1)])
        return Pose(fall=f, lean=14-10*f, hand_x=47-13*f, hand_y=-90+32*f, jaw=1+2*f)
    raise ValueError(anim)


def _render_frame(anim, i, n):
    q=pose(anim,i,n)
    d=Canvas(FRAME_SIZE)
    # Keep the body-root and the ground independent of the torso sway.
    def P(x,y): return add((CX-8*q.recoil+60*q.fall, GROUND+1-18*q.fall),rot((x,y),-80*q.fall))
    def B(x,y): return P(*add((0,-65+q.bob),rot((x,y+65),q.lean)))
    def poly(pts,c,edge=INK,w=1.6): d.poly([B(*p) for p in pts],c,edge,w)
    def line(pts,c,w=1.5): d.line([B(*p) for p in pts],c,w)
    def oval(x,y,rx,ry,c,edge=INK,w=1.3): d.oval(B(x,y),rx,ry,c,edge,w,q.lean-80*q.fall)

    # The shroud hangs behind the torso, with long strips of ragged linen.
    poly([(-20,-116),(-8,-111),(-18,-63),(-27+q.rag,-25),(-36+q.rag,-36),
          (-43+q.rag,-30),(-41,-59),(-34,-95)],LINEN_D)
    poly([(-22,-111),(-19,-80),(-32+q.rag,-40),(-36+q.rag,-44),(-30,-80)],LINEN,None)
    line([(-27,-101),(-33,-76),(-38+q.rag,-46)],LINEN_L,1.4)

    # Far leg drags; near leg plants. Asymmetric cloth and bare shin.
    for far,side in ((True,-1),(False,1)):
        p=q.ph+(math.pi if far else 0)
        step=(13 if far else 23)*q.stride*math.sin(p)
        lift=(3 if far else 11)*q.stride*max(0,math.cos(p))
        hip=B(side*9,-65)
        knee=P(side*11+step*.48,-32-lift*.4)
        ankle=P(side*12+step,-7-lift)
        d.tube(hip,knee,9 if far else 10,CLOTH_D if far else LINEN,LINEN_D if far else LINEN_L)
        d.disk(knee,6.4,SKIN_D if far else SKIN,INK,1.3)
        d.tube(knee,ankle,5.5,SKIN_D if far else SKIN,SKIN if far else SKIN_L,DEEP)
        if far:
            for a in (.12,.32,.52,.72):
                d.tube(mix(knee,ankle,a),mix(knee,ankle,a+.10),6.8,LINEN_D,LINEN)
        else:
            d.tube(mix(knee,ankle,.15),mix(knee,ankle,.48),3,BONE,None,SKIN_D,None)
        x=side*12+step; y=-lift
        foot=[P(x-7,y-11),P(x+5,y-11),P(x+8,y-7),P(x+18,y-5),P(x+19,y-1),P(x-8,y-1)]
        d.poly(foot,SKIN_D if far else SKIN,INK,1.4)
        for a in (11,15): d.line([P(x+a,y-5),P(x+a-1,y-1)],DEEP,.9)

    # Far reaching arm, behind the chest.
    sh=B(13,-111); el=B(25,-87); hand=P(q.far_x,q.far_y)
    d.tube(sh,el,7.3,SKIN_D,SKIN); d.disk(el,5.8,SKIN_D,INK,1.1)
    d.tube(el,hand,4.7,SKIN_D,SKIN); d.oval(hand,7,5,SKIN_D,INK,1.2)
    def H(x,y): return add(hand,rot((x,y),-80*q.fall))
    for j in range(3): d.line([H(3,-3+j*3),H(12,-1+j*3)],SKIN_D,2.9)

    # Unarmored body: rope-tied burial tunic, torn hem and visible ribs.
    poly([(-23,-113),(-7,-122),(12,-120),(24,-108),(19,-91),(13,-67),(21,-45),
          (9,-50),(4,-43),(-8,-48),(-16,-43),(-24,-52),(-22,-75),(-26,-96)],LINEN)
    poly([(-23,-111),(-20,-89),(-17,-65),(-23,-51),(-16,-43),(-8,-48),(-8,-65),(-13,-97)],LINEN_D,None)
    poly([(3,-112),(20,-109),(18,-94),(11,-90),(4,-97),(-1,-101)],SKIN_D)
    for j in range(3): line([(6,-107+j*5),(15,-106+j*5)],BONE,2.1)
    # Broad irregular overlapping folds suggest a burial shroud, not a uniform.
    poly([(-24,-108),(-16,-114),(15,-98),(16,-93),(-15,-99),(-25,-101)],LINEN_L,LINEN_D,1)
    poly([(-23,-91),(-18,-96),(15,-82),(15,-77),(-19,-85)],LINEN_L,LINEN_D,1)
    line([(-20,-77),(-7,-74),(12,-76)],LINEN_D,3.0)
    line([(-20,-78),(-7,-75),(12,-77)],LINEN_L,1.3)
    oval(-5,-75,4,3,LINEN_D)
    line([(-6,-72),(-10,-64),(-10,-59)],LINEN_D,2.2)
    line([(-4,-72),(2,-62),(0,-56)],LINEN_D,2.2)
    line([(-10,-65),(-13,-56),(-17,-50)],LINEN_D,1.3)
    line([(7,-66),(10,-55)],LINEN_D,1.2)

    # Head: slack jaw, sunken cheeks, one torn strip across the crown.
    poly([(-7,-123),(13,-123),(16,-114),(5,-108),(-8,-115)],SKIN_D)
    oval(8,-138,21,23,SKIN)
    poly([(-10,-153),(-12,-140),(-6,-125),(4,-120),(17,-123),(25,-132),(24,-145),(19,-152)],SKIN)
    poly([(-10,-151),(-8,-137),(-1,-133),(-2,-126),(-9,-130),(-13,-141)],SKIN_D,None)
    poly([(-3,-147),(5,-151),(14,-147),(11,-144),(0,-144)],SKIN_L,None)
    # Large dark orbital shapes read clearly at small scale.
    poly([(-2,-143),(8,-146),(15,-141),(12,-135),(3,-135),(-2,-138)],DEEP)
    if q.fall<.93: oval(7,-141,3.7*(1-q.fall),3.2*(1-q.fall),EYE,None)
    poly([(20,-145),(25,-144),(26,-139),(21,-136),(18,-139)],DEEP)
    if q.fall<.93: oval(23,-141,2.2*(1-q.fall),2.1*(1-q.fall),EYE,None)
    poly([(16,-140),(22,-134),(18,-131),(13,-134)],SKIN_L,SKIN_D,1.1)
    poly([(4,-130),(16,-131),(25,-128),(23,-122+q.jaw),(15,-118+q.jaw),(6,-121+q.jaw)],MOUTH)
    for x in (8,12,16,20):
        poly([(x,-130),(x+3,-130),(x+3,-125),(x,-126)],BONE,None)
    line([(7,-121+q.jaw),(15,-118+q.jaw),(23,-122+q.jaw)],SKIN,4)
    # A few wisps of hair and a torn forehead wrap.
    poly([(-10,-153),(-9,-160),(-4,-155),(0,-164),(4,-158),(11,-160),(17,-154),(5,-151)],HAIR)
    poly([(-11,-153),(-4,-157),(15,-155),(23,-151),(21,-146),(9,-148),(-9,-147)],LINEN,LINEN_D,1)
    line([(-7,-152),(4,-154),(16,-151)],LINEN_L,1.8)
    line([(-10,-149),(-16,-140),(-17,-132)],LINEN_D,3.0)

    # Near arm is held in a crooked reach. The sleeve has unravelled.
    sh=B(-20,-109); el=P(q.elbow_x,q.elbow_y); hand=P(q.hand_x,q.hand_y)
    d.tube(sh,el,8.1,SKIN,SKIN_L,SKIN_D)
    d.tube(sh,mix(sh,el,.58),9.4,LINEN,LINEN_L,LINEN_D)
    d.disk(el,6.6,SKIN,INK,1.2)
    d.tube(el,hand,5.8,SKIN,SKIN_L,SKIN_D)
    # A strip of loose linen visibly trails the forearm rather than floating.
    start=mix(el,hand,.28); end=mix(el,hand,.47)
    d.tube(start,end,7,LINEN_D,LINEN_L)
    d.poly([start,end,add(end,(-4+q.rag,15)),add(end,(-11+q.rag,12)),add(start,(-4,6))],LINEN,INK,1.1)
    d.oval(hand,7.3,6.5,SKIN,INK,1.3,-80*q.fall)
    for j, length in enumerate((9,13,12,8)):
        base=H(4,-5+j*3)
        tip=H(length+5,-4+j*3+max(0,j-1)*2)
        mid=mix(base,tip,.72)
        d.line([base,mid,tip],INK,3.5)
        d.line([base,mid,tip],SKIN_L if j<2 else SKIN,2.3)
    d.line([H(1,3),H(6,9)],INK,3.9)
    d.line([H(1,3),H(6,9)],SKIN,2.6)
    im=d.finish()
    return anchored_death(im,GROUND) if q.fall>0 else im


def _body_metrics(fw,fh):
    # Arms and trailing linen are presentation, not the collision body.
    return body_metrics_for_box((CX-20,34,CX+36,GROUND+1),fw,fh)


def render(out_dir: str | Path, **opts):
    out_dir=Path(out_dir)
    out_dir.mkdir(parents=True,exist_ok=True)
    outputs=build_sheet(target=TARGET_NAME,rows=ROWS,render_fn=_render_frame,
                        out_dir=out_dir,frame_size=FRAME_SIZE,auto_crop=False,
                        actor_metadata=ACTOR_METADATA,body_metrics_fn=_body_metrics,
                        animation_key_map={a:a for a,_,_ in ROWS},sits_on_ground=True)
    return [outputs[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]
