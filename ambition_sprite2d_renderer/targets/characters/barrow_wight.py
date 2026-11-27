"""Barrow Wight: an old burial guard with a broken grave marker for a maul.

The wight lifts the maul before it strikes, then pulls it off the floor.
The weapon and cloak are not part of the body box. No ground shadow.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

from ._clockwork_enemy_art import (
    Canvas, add, mix, phase, rot, track, anchored_death,
)
from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box

TARGET_NAME = "barrow_wight"
DISPLAY_NAME = "Barrow Wight"
FRAME_SIZE = (320, 288)
CX, GROUND = 133.0, 252.0
WINDUP_S, ACTIVE_S, RECOVER_S = 0.64, 0.16, 0.8
ROWS = [
    ("idle", 12, 120), ("walk", 12, 105), ("run", 12, 85),
    ("notice", 8, 90), ("windup", 8, 80), ("attack_side", 32, 50),
    ("hit", 5, 85), ("death", 14, 90),
]
LOOPS = {"idle", "walk", "run", "windup"}
TRAITS = ["enemy", "undead", "barrow", "armored", "combatant"]
ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": DISPLAY_NAME},
    "body": {"body_plan": "HumanoidBiped", "body_kind": "Standard",
             "mass_class": "Medium", "locomotion_hint": "Walk", "traits": TRAITS},
    "brain": {"default_preset": "melee_brute_striker"},
    "actions": {"default_preset": "barrow_wight_slam"},
    "visual": {"default_pose": "idle", "portrait": {"animation": "idle", "frame": 0}},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "action.melee.primary": {"animation": "attack_side", "events": [
            {"t": WINDUP_S / (WINDUP_S + ACTIVE_S + RECOVER_S),
             "event": "hitbox_active_start", "source": "barrow_wight.slam"},
            {"t": (WINDUP_S + ACTIVE_S) / (WINDUP_S + ACTIVE_S + RECOVER_S),
             "event": "hitbox_active_end", "source": "barrow_wight.slam"},
        ]},
        "combat.hurt": {"animation": "hit", "events": []},
        "combat.death": {"animation": "death", "events": []},
    },
    "tags": TRAITS,
    "authoring_description": "An ancient burial guard with a cracked bronze helmet, faded burial cloth, exposed bones and a broken grave marker on a short haft.",
    "gameplay_description": "A slow guard with a long overhead tell, a heavy downward strike and a long recovery. Stronger than an ordinary risen corpse, weaker than the Barrow King.",
}

INK = '#292329'
DARK = '#39383b'
BONE = '#c5b99b'
BONE_L = '#ece0bc'
BONE_D = '#817a69'
BRONZE = '#98794c'
BRONZE_L = '#d5b47b'
BRONZE_D = '#5b4c3d'
PATINA = '#59766a'
IRON = '#666763'
IRON_D = '#454947'
CLOTH = '#704652'
CLOTH_L = '#9b6266'
CLOTH_D = '#49313f'
STONE = '#81877d'
STONE_L = '#b6b6a2'
STONE_D = '#4d5754'
MOSS = '#657457'
EYE = '#93e3c9'
EYE_L = '#e2fff0'
WOOD = '#72543c'
WOOD_L = '#b38b59'


@dataclass(frozen=True)
class Pose:
    lean: float = 4.0
    bob: float = 0.0
    stride: float = 0.0
    ph: float = 0.0
    hand_x: float = 36.0
    hand_y: float = -65.0
    weapon_angle: float = 36.0
    cloth: float = 0.0
    recoil: float = 0.0
    fall: float = 0.0
    light: float = 1.0


def pose(anim, i, n):
    t = phase(i, n, anim in LOOPS)
    p = math.tau * t
    if anim == 'idle':
        return Pose(bob=1.4*math.sin(p), cloth=2*math.sin(p))
    if anim in ('walk', 'run'):
        st = .75 if anim == 'walk' else 1.0
        return Pose(lean=8, bob=-2.8*abs(math.sin(p)), stride=st, ph=p,
                    hand_y=-68+3*math.sin(p), weapon_angle=31+5*math.sin(p), cloth=5*math.sin(p))
    if anim == 'notice':
        return Pose(lean=4-12*math.sin(math.pi*t), hand_y=-65-10*math.sin(math.pi*t),
                    weapon_angle=36-12*math.sin(math.pi*t), cloth=5*math.sin(math.pi*t))
    if anim == 'windup':
        # Match the held startup pose in the attack row.
        return Pose(lean=-9, bob=-2, hand_x=10, hand_y=-151+1.3*math.sin(p),
                    weapon_angle=-125+2*math.sin(p), cloth=-6)
    if anim == 'attack_side':
        a = WINDUP_S / (WINDUP_S + ACTIVE_S + RECOVER_S)
        b = (WINDUP_S + ACTIVE_S) / (WINDUP_S + ACTIVE_S + RECOVER_S)
        impact = a+.045
        def k(keys): return track(t, keys)
        return Pose(
            lean=k([(0,-9),(a,-9),(impact,24),(b,24),(.76,17),(1,4)]),
            bob=k([(0,-2),(a,-2),(impact,7),(b,7),(.76,5),(1,0)]),
            hand_x=k([(0,10),(a,10),(impact,48),(b,48),(.76,42),(1,36)]),
            hand_y=k([(0,-151),(a,-151),(impact,-56),(b,-56),(.76,-58),(1,-65)]),
            weapon_angle=k([(0,-125),(a,-125),(impact,32),(b,32),(.76,31),(1,36)]),
            cloth=k([(0,-6),(a,-6),(impact,12),(.75,8),(1,0)]),
        )
    if anim == 'hit':
        r=math.sin(math.pi*t)
        return Pose(lean=4-22*r, bob=-4*r, recoil=r, hand_y=-65-10*r, weapon_angle=36+13*r)
    if anim == 'death':
        f=track(t,[(0,0),(.16,0),(.8,1),(1,1)])
        return Pose(fall=f, recoil=.3, light=1-f, weapon_angle=40-20*f)
    raise ValueError(anim)


def _render_frame(anim, i, n):
    q=pose(anim,i,n)
    d=Canvas(FRAME_SIZE)
    def P(x,y): return add((CX-8*q.recoil+89*q.fall,GROUND-2-25*q.fall), rot((x,y), -83*q.fall))
    def B(x,y): return P(*add((0,-72+q.bob),rot((x,y+72),q.lean)))
    def poly(pts,c,edge=INK,w=1.6): d.poly([B(*p) for p in pts],c,edge,w)
    def line(pts,c,w=1.5): d.line([B(*p) for p in pts],c,w)
    def oval(x,y,rx,ry,c,edge=INK,w=1.4): d.oval(B(x,y),rx,ry,c,edge,w,q.lean-83*q.fall)

    # The rear cloth hangs from the shoulders. The torn hem moves with the pose.
    poly([(-28,-133),(-11,-130),(-15,-67),(-24+q.cloth,-21),(-36+q.cloth,-31),
          (-43+q.cloth,-19),(-50+q.cloth,-37),(-53+q.cloth,-30),(-49,-83)],CLOTH_D)
    poly([(-28,-130),(-34,-78),(-43+q.cloth,-35),(-32+q.cloth,-43),(-23,-82),(-18,-128)],CLOTH,None)
    line([(-36,-112),(-44,-76),(-45+q.cloth,-44)],CLOTH_L,1.8)

    # Legs: dark mail, exposed shin bone, bronze greaves, worn feet.
    for side,far in ((-1,True),(1,False)):
        a=q.ph+(math.pi if far else 0)
        step=22*q.stride*math.sin(a)
        lift=12*q.stride*max(0,math.cos(a))
        hip=B(side*13,-69); knee=P(side*14+step*.46,-36-lift*.35)
        ankle=P(side*15+step,-8-lift)
        d.tube(hip,knee,10,IRON_D if far else DARK,IRON)
        d.disk(knee,9,BRONZE_D if far else BRONZE,INK,1.2)
        d.tube(knee,ankle,6.5,BONE_D if far else BONE,BONE_L,BONE_D)
        d.tube(mix(knee,ankle,.12),mix(knee,ankle,.7),8,BRONZE_D if far else BRONZE,BRONZE_L,PATINA)
        foot=[P(side*15+step-9,-12-lift),P(side*15+step+7,-12-lift),
              P(side*15+step+19,-5-lift),P(side*15+step+17,-1-lift),
              P(side*15+step-11,-1-lift),P(side*15+step-12,-6-lift)]
        d.poly(foot,IRON_D if far else BRONZE_D,INK,1.8)
        d.line(foot[2:4],BRONZE_L,1.5)

    # Far arm, partially hidden behind the chest, reaches for the maul.
    sh=B(18,-125); el=B(35,-101); wr=B(25,-82)
    d.tube(sh,el,9,IRON_D,IRON); d.tube(el,wr,5.8,BONE_D,BONE)
    d.disk(wr,6.5,BONE_D,INK,1.2)

    # Burial skirt, segmented bronze cuirass, and exposed damaged side.
    poly([(-28,-80),(23,-80),(29,-46),(19,-51),(13,-43),(1,-50),(-13,-43),(-22,-50),(-31,-43)],CLOTH)
    for x in (-22,-10,3,16):
        poly([(x,-76),(x+10,-76),(x+9,-55),(x+3,-51),(x-1,-57)],BRONZE_D)
        line([(x+1,-73),(x+7,-73)],BRONZE_L,1.1)
    poly([(-26,-131),(-9,-141),(14,-141),(31,-127),(25,-98),(17,-77),(-25,-77),(-32,-100)],BRONZE)
    poly([(-26,-131),(-19,-126),(-16,-91),(-25,-77),(-32,-100)],BRONZE_D,None)
    poly([(-12,-134),(12,-134),(24,-123),(17,-112),(-7,-111),(-15,-120)],BRONZE_L,INK,1.0)
    poly([(-8,-111),(17,-112),(14,-101),(-6,-98)],BRONZE,BRONZE_D,1.2)
    poly([(-6,-98),(15,-101),(12,-91),(-10,-87)],BRONZE,BRONZE_D,1.2)
    # Broken armor shows three ribs; a patch of green patina follows its edge.
    poly([(19,-119),(30,-120),(25,-99),(19,-93),(11,-97),(17,-105)],DARK)
    for y in (-115,-110,-105): line([(20,y),(26,y-2)],BONE,2.0)
    poly([(-28,-108),(-22,-105),(-24,-99),(-18,-91),(-26,-89),(-30,-98)],PATINA,None)
    line([(-3,-132),(1,-126),(-4,-119)],BRONZE_D,1.4)
    poly([(-28,-82),(22,-82),(24,-74),(-29,-74)],BRONZE_D)
    oval(0,-78,6,5,BRONZE_L); oval(0,-78,2,2,PATINA,None)
    # Faded scarf over the collar.
    poly([(-21,-144),(-10,-148),(15,-145),(23,-136),(13,-130),(-19,-132),(-28,-137)],CLOTH)
    line([(-19,-139),(0,-135),(17,-138)],CLOTH_L,2)

    # Skull and pointed nasal guard. The large dark sockets read at game scale.
    oval(4,-160,23,23,BONE)
    poly([(-11,-161),(-7,-145),(3,-139),(17,-142),(22,-150),(27,-151),(29,-157),(23,-164)],BONE)
    poly([(-7,-150),(4,-142),(17,-144),(21,-150),(5,-151)],BONE_D,None)
    for x in (3,7,11,15): line([(x,-147),(x,-143)],INK,.9)
    oval(5,-161,8.2,5.5,DARK); oval(21,-163,5.1,4.7,DARK)
    if q.light > .1:
        oval(7,-161,3.6*q.light,3.1*q.light,EYE,None)
        oval(22,-163,2.7*q.light,2.5*q.light,EYE,None)
        oval(8,-162,1.3,1.3,EYE_L,None)
    poly([(14,-157),(11,-152),(17,-152)],INK,None)
    # Ancient bronze helmet with a split rim, cheek plates and a hammered crest.
    poly([(-22,-164),(-25,-177),(-17,-190),(-3,-195),(12,-192),(24,-184),(29,-173),
          (24,-169),(17,-172),(12,-166),(-6,-165),(-9,-150),(-19,-153)],BRONZE)
    poly([(-23,-177),(-17,-190),(-3,-195),(12,-192),(19,-186),(-2,-189),(-15,-181)],BRONZE_L,None)
    poly([(-22,-173),(-10,-169),(-9,-150),(-19,-153)],BRONZE_D)
    poly([(19,-179),(26,-177),(29,-172),(18,-171),(14,-161),(10,-165),(12,-174)],BRONZE_L)
    poly([(-20,-181),(-14,-184),(-10,-178),(-15,-172),(-21,-174)],PATINA,None)
    line([(-1,-193),(1,-183),(-4,-179),(2,-173)],BRONZE_D,1.6)
    for x,y in [(-18,-169),(-12,-165),(19,-175)]: oval(x,y,1.8,1.8,BRONZE_L,INK,.8)

    # The near arm and the maul use the same wrist. The grave marker is a
    # chipped block of stone, not a steel blade or a shield.
    sh=B(-24,-125)
    raise_arm=max(0.,min(1.,(-q.hand_y-65)/86))
    elbow=B(2-32*raise_arm,-91-31*raise_arm)
    hand=P(q.hand_x,q.hand_y)
    d.tube(sh,elbow,10,IRON_D,IRON)
    d.oval(sh,15,12,BRONZE,INK,1.7,q.lean-83*q.fall)
    d.line([add(sh,(-9,-3)),add(sh,(0,-8)),add(sh,(9,-4))],BRONZE_L,2.0)
    d.disk(elbow,7,BRONZE_D,INK,1.2)
    d.tube(elbow,hand,6.5,BONE,BONE_L,BONE_D)
    d.tube(mix(elbow,hand,.38),mix(elbow,hand,.73),8,BRONZE,BRONZE_L,PATINA)
    angle=q.weapon_angle-83*q.fall
    def W(x,y):return add(hand,rot((x,y),angle))
    d.tube(W(-16,0),W(47,0),4.5,WOOD,WOOD_L,BRONZE_D)
    for x in (-12,-7,19,24,29):d.line([W(x,-4),W(x+1,4)],BRONZE_D,1.8)
    slab=[(33,-15),(43,-21),(71,-21),(86,-12),(80,-3),(88,7),(77,19),(46,19),(35,12)]
    d.poly([W(*p) for p in slab],STONE,INK,2.2)
    d.poly([W(*p) for p in [(33,-15),(43,-21),(71,-21),(86,-12),(77,-10),(44,-12)]],STONE_L,None)
    d.poly([W(*p) for p in [(35,12),(46,19),(77,19),(88,7),(80,5),(72,12),(47,13)]],STONE_D,None)
    d.poly([W(*p) for p in [(39,-10),(44,-14),(67,-14),(77,-6),(73,10),(43,10)]],STONE_L,STONE_D,1)
    # Carved arch and a cracked burial inscription.
    d.line([W(49,6),W(49,-4),W(55,-9),W(61,-4),W(61,6)],STONE_D,2.4)
    d.line([W(65,-6),W(69,-6),W(68,2),W(72,5)],STONE_D,1.6)
    d.line([W(75,-14),W(70,-6),W(76,-1),W(70,8),W(75,15)],STONE_D,1.7)
    for x,y,r in [(43,14,3),(47,15,3),(70,-18,2.6),(74,-15,2.5)]:d.disk(W(x,y),r,MOSS,None)
    d.oval(hand,7.7,7.3,BONE,INK,1.5,angle)
    for k in range(3): d.line([W(-4+k*3,-4),W(-4+k*3,2)],BONE_D,1)

    # A small attached impact burst marks the instant the stone lands.
    if anim=='attack_side' and .445 <= i/max(1,n-1) <= .52:
        at=W(83,8)
        for v in ((17,-16),(25,-4),(19,4)):
            d.line([add(at,(v[0]*.3,v[1]*.3)),add(at,v)],STONE_L,2)
    im=d.finish()
    return anchored_death(im,GROUND) if q.fall>0 else im


def _body_metrics(fw,fh):
    return body_metrics_for_box((98,53,166,GROUND+1),fw,fh)


def render(out_dir: str | Path, **opts):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs=build_sheet(target=TARGET_NAME, rows=ROWS, render_fn=_render_frame,
        out_dir=Path(out_dir), frame_size=FRAME_SIZE, auto_crop=False,
        actor_metadata=ACTOR_METADATA, body_metrics_fn=_body_metrics,
        animation_key_map={a:a for a,_,_ in ROWS}, sits_on_ground=True)
    return [outputs[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]
