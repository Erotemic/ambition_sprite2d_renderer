"""Procedural full-action renderer for Hypatia Prime.

Hypatia Prime is a science-fantasy mystery character inspired by Hypatia of
Alexandria: mathematician, astronomer, philosopher, teacher, and historical
person whose surviving record is fragmentary and heavily refracted through
later retellings. The design does not pretend to reveal a definitive private
personality or appearance. Instead, the playable figure is an enigmatic
scholar-guardian assembled from incomplete sources, copied diagrams, missing
folios, and several mutually incompatible legends.

Her silhouette combines a midnight scholar's mantle, bronze lamellar panels,
a partially veiled face, an astrolabe halo, and a staff built from an armillary
ring. During major actions faint alternate silhouettes appear behind her—scribe,
astronomer, lecturer, and armored guardian—then fail to settle into one answer.
Everything is rendered with supersampled Pillow geometry and publishes through
Ambition's normal character target contract.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw

from ...authoring.portrait import PortraitClip, write_portrait_sheet
from ...authoring.sheet_build import build_sheet, write_canonical
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "hypatia_prime"
FRAME_W = 128
FRAME_H = 128
SUPER = 4
PORTRAIT_SIZE = (192, 192)

AUTHORING_DESCRIPTION = {
    "parody_of": "Hypatia of Alexandria",
    "character_name": "Hypatia Prime",
    "concept": (
        "An enigmatic scholar-guardian inspired by Hypatia of Alexandria. The character "
        "is intentionally presented through incomplete records and competing reconstructions: "
        "a mathematician, astronomer, philosopher, teacher, librarian, and possibly something "
        "more within the game's fiction, but never reduced to a single definitive legend."
    ),
    "name_origin": (
        "Prime suggests a primary or ideal reconstruction among many later versions, while also "
        "giving the character a mathematical and science-fiction title. The game should never "
        "confirm that this reconstruction is the uniquely true one."
    ),
    "historical_mystery": (
        "Much of Hypatia's own work is lost and the surviving evidence is indirect, sparse, and "
        "filtered through later political, religious, literary, and philosophical narratives. "
        "The character's mystery should reflect that problem of historical reconstruction rather "
        "than inventing secret facts about the real person."
    ),
    "visual_inspiration": [
        "A bronze astrolabe halo identifies astronomy and instrument-making while hiding part of the head silhouette.",
        "A layered midnight mantle and palimpsest veil make the figure look copied, revised, and partially erased.",
        "An armillary staff functions as a spear, pointer, measuring instrument, and portable celestial model.",
        "Faint alternate silhouettes appear during special moves but never resolve into one canonical appearance.",
        "Scroll fragments carry conic curves, star positions, and incomplete geometric constructions rather than legible modern formulas.",
    ],
    "gameplay_inspiration": [
        "astrolabe_guard rotates a bronze instrument into a precise defensive alignment.",
        "conic_lance traces ellipse, parabola, and hyperbola arcs before the staff commits to one line of attack.",
        "epicycle_orbit surrounds the character with small nested celestial paths that redirect projectiles.",
        "library_of_shadows calls several incompatible reconstructed silhouettes into the arena.",
        "missing_folio scatters incomplete pages whose gaps become dangerous zones.",
        "prime_revelation aligns the fragments into a momentary radiant model, but still leaves the face obscured.",
    ],
    "gameplay_description": (
        "A precise midrange scholar-knight built around counterplay, orbiting defenses, and delayed "
        "geometric attacks. Hypatia Prime controls space with the armillary staff and astrolabe, then "
        "uses missing fragments to create ambiguity about where the real strike will land. Her strongest "
        "moves briefly align several incomplete reconstructions without ever resolving the character's mystery."
    ),
    "suggested_barks": {
        "idle": [
            "The record is incomplete. That is not permission to stop reading.",
            "A copy of a copy can still preserve an angle.",
            "You expected certainty from fragments?",
        ],
        "combat": [
            "Observe before you conclude.",
            "The orbit closes.",
            "Choose your reconstruction carefully.",
            "The missing line still has consequences.",
        ],
        "on_hit": [
            "Add that to the surviving testimony.",
            "An inelegant correction.",
        ],
        "victory": [
            "One account survives. Not the only one.",
            "The diagram is clearer than the legend.",
        ],
    },
    "fallback_dialogue": [
        "You are speaking to a reconstruction. Whether I am the first, the best, or merely the latest is another question.",
        "Most people remember the ending because endings travel easily. I am more interested in the work that did not survive.",
        "A missing book is not an empty book. It leaves citations, students, arguments, and strangely shaped absences.",
        "Every age redraws me in its own clothing. I have learned to keep several wardrobes.",
        "Mystery is not magic. Sometimes it is simply what remains after the documents do not.",
    ],
    "boundaries": [
        "Do not claim that the game's mysterious details are newly discovered facts about the historical Hypatia.",
        "Do not define her primarily by the violence of her death; center teaching, mathematics, astronomy, philosophy, and lost work.",
        "Avoid flattening complex late-antique history into a single modern culture-war allegory.",
        "The obscured face and conflicting silhouettes should communicate incomplete evidence, not shame or passivity.",
        "Keep Hypatia Prime formidable, intellectually active, and capable of correcting the legends projected onto her.",
    ],
}

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 150),
    ("walk", 8, 106),
    ("run", 8, 82),
    ("crouch", 6, 96),
    ("jump", 6, 90),
    ("fall", 6, 94),
    ("land_hard", 6, 88),
    ("dash", 7, 66),
    ("roll", 8, 66),
    ("block", 6, 82),
    ("hit", 5, 86),
    ("death", 8, 112),
    ("talk", 8, 106),
    ("interact", 8, 96),
    ("astrolabe_guard", 8, 72),
    ("conic_lance", 10, 68),
    ("epicycle_orbit", 10, 76),
    ("library_of_shadows", 12, 78),
    ("missing_folio", 10, 80),
    ("prime_revelation", 12, 74),
    ("celebrate", 8, 92),
    ("taunt", 8, 98),
]

ACTOR_METADATA = {
    "actor": {"character_id": "npc_hypatia_prime", "display_name": "Hypatia Prime"},
    "authoring_description": AUTHORING_DESCRIPTION,
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": [
            "story", "humanoid", "mathematician", "astronomer", "philosopher",
            "scholar_guardian", "mystery", "playable_candidate",
        ],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {
            "walk": True, "jump": True, "climb": True, "fly": None,
            "swim": True, "crawl": True, "use_lifts": True,
            "door_access": ["public", "archive"],
        },
        "interactions": {
            "talk": True, "trade": None, "carry": True,
            "open_doors": ["public", "archive"],
        },
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "visual": {
        "default_pose": "idle",
        "portrait": {"face_guide": {
            "center": {"x": 63.0, "y": 31.0},
            "size": {"w": 34.0, "h": 38.0},
            "source_size": {"w": 128.0, "h": 128.0},
        }},
    },
    "tags": [
        "story", "humanoid", "mathematician", "astronomer", "philosopher",
        "scholar_guardian", "mystery", "playable_candidate",
    ],
    "sockets": {
        "head": {"source": "explicit.hypatia_prime", "point": {"x": 63.0, "y": 31.0}},
        "chest": {"source": "explicit.hypatia_prime", "point": {"x": 63.0, "y": 61.0}},
        "hand_l": {"source": "explicit.hypatia_prime", "point": {"x": 43.0, "y": 69.0}},
        "hand_r": {"source": "explicit.hypatia_prime", "point": {"x": 83.0, "y": 67.0}},
        "staff_tip": {"source": "explicit.hypatia_prime", "point": {"x": 102.0, "y": 24.0}},
        "speech_bubble": {"source": "explicit.hypatia_prime", "point": {"x": 63.0, "y": 3.0}},
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "action.melee.primary": {"animation": "conic_lance", "events": []},
        "action.special.primary": {"animation": "epicycle_orbit", "events": []},
        "action.special.secondary": {"animation": "library_of_shadows", "events": []},
        "action.special.tertiary": {"animation": "missing_folio", "events": []},
        "action.defense.block": {"animation": "astrolabe_guard", "events": []},
        "action.defense.roll": {"animation": "roll", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
    },
    "provenance": {
        "variant_family": TARGET_NAME,
        "variant_id": "gpt_5_6_thinking_original_2026_07_26",
        "lineage": [
            {
                "revision_id": "hypatia_prime_concept_direction",
                "creator_kind": "human",
                "creator": "Jon Crall",
                "contribution": "selected_hypatia_prime_and_requested_mystery_reflecting_the_fragmentary_historical_person",
            },
            {
                "revision_id": "hypatia_prime_procedural_sprite_v1",
                "creator_kind": "model",
                "creator": "gpt-5.6-thinking",
                "parent_revision_id": "hypatia_prime_concept_direction",
                "contribution": "procedural_full_action_mysterious_scholar_guardian_with_portraits_barks_and_historical_boundaries",
            },
        ],
    },
}

OUTLINE = (18, 19, 30, 255)
OUTLINE_SOFT = (45, 45, 66, 255)
SKIN = (177, 117, 83, 255)
SKIN_LIGHT = (226, 165, 117, 255)
SKIN_SHADE = (119, 72, 63, 255)
HAIR = (27, 25, 35, 255)
INDIGO = (35, 34, 78, 255)
INDIGO_LIGHT = (58, 62, 119, 255)
MIDNIGHT = (25, 28, 52, 255)
PURPLE = (78, 45, 101, 255)
BRONZE = (171, 112, 48, 255)
BRONZE_LIGHT = (231, 184, 87, 255)
PARCHMENT = (226, 211, 167, 255)
INK = (67, 49, 53, 255)
CYAN = (82, 207, 218, 255)
STAR = (247, 231, 164, 255)
SHADOW_A = (80, 158, 191, 255)
SHADOW_B = (173, 94, 175, 255)
SHADOW_C = (205, 151, 70, 255)


def _fade(color: RGBA, alpha: float) -> RGBA:
    return color[:3] + (max(0, min(255, int(color[3] * alpha))),)


def _p(point: Point) -> Tuple[int, int]:
    return (round(point[0] * SUPER), round(point[1] * SUPER))


def _line(draw: ImageDraw.ImageDraw, points: Sequence[Point], fill: RGBA, width: float=1.0) -> None:
    draw.line([_p(p) for p in points], fill=fill, width=max(1,round(width*SUPER)), joint="curve")


def _ellipse(draw: ImageDraw.ImageDraw, box: Tuple[float,float,float,float], fill: RGBA, outline: RGBA|None=None, width: float=1.0) -> None:
    b=tuple(round(v*SUPER) for v in box)
    draw.ellipse(b,fill=fill,outline=outline,width=max(1,round(width*SUPER)) if outline else 1)


def _poly(draw: ImageDraw.ImageDraw, points: Sequence[Point], fill: RGBA, outline: RGBA|None=None, width: float=1.0) -> None:
    pts=[_p(p) for p in points]
    draw.polygon(pts,fill=fill)
    if outline:
        draw.line(pts+[pts[0]],fill=outline,width=max(1,round(width*SUPER)),joint="curve")


def _arc(draw: ImageDraw.ImageDraw, box: Tuple[float,float,float,float], start: float,end: float,fill: RGBA,width: float=1.0) -> None:
    b=tuple(round(v*SUPER) for v in box)
    draw.arc(b,start=start,end=end,fill=fill,width=max(1,round(width*SUPER)))


def _capsule(draw: ImageDraw.ImageDraw,a:Point,b:Point,radius:float,fill:RGBA,outline:RGBA=OUTLINE)->None:
    _line(draw,[a,b],outline,radius*2+2)
    _line(draw,[a,b],fill,radius*2)


@dataclass(frozen=True)
class Pose:
    phase: float
    x: float=0.0
    y: float=0.0
    lean: float=0.0
    squat: float=0.0
    arm_l: float=0.0
    arm_r: float=0.0
    foot_l: float=0.0
    foot_r: float=0.0
    staff: float=-15.0
    veil: float=0.0
    power: float=0.0
    expression: int=0
    anim: str="idle"


def _pose(anim:str,frame_idx:int,nframes:int)->Pose:
    t=frame_idx/max(1,nframes)
    wave=math.sin(t*math.tau)
    p=Pose(t,y=wave*.8,arm_l=-wave*4,arm_r=wave*4,staff=-12+wave*2,veil=.15+.05*wave,anim=anim)
    if anim=="walk": p=Pose(t,y=abs(wave)*1.2,lean=2,arm_l=-wave*15,arm_r=wave*12,foot_l=wave*8,foot_r=-wave*8,staff=-10+wave*4,veil=.25,anim=anim)
    elif anim=="run": p=Pose(t,y=abs(wave)*2,lean=10,arm_l=-wave*22,arm_r=wave*18,foot_l=wave*13,foot_r=-wave*13,staff=18,veil=.65,anim=anim)
    elif anim=="crouch": p=Pose(t,y=4,squat=8,arm_l=-15,arm_r=12,staff=-2,veil=.2,anim=anim)
    elif anim=="jump": p=Pose(t,y=-8*math.sin(t*math.pi),lean=-4+7*t,arm_l=-20,arm_r=18,foot_l=-7,foot_r=7,staff=-30,veil=.5,anim=anim)
    elif anim=="fall": p=Pose(t,y=-1+6*t,lean=6,arm_l=24,arm_r=-18,foot_l=5,foot_r=-5,staff=25,veil=.75,anim=anim)
    elif anim=="land_hard":
        k=math.sin(t*math.pi); p=Pose(t,y=4*k,squat=11*k,arm_l=-30*k,arm_r=27*k,staff=-5,veil=.35,power=k,anim=anim)
    elif anim=="dash": p=Pose(t,x=3*math.sin(t*math.pi),lean=18,arm_l=-30,arm_r=22,foot_l=10*wave,foot_r=-10*wave,staff=42,veil=.9,anim=anim)
    elif anim=="roll": p=Pose(t,y=7,squat=16,lean=t*360,arm_l=-25,arm_r=25,staff=t*360,veil=.7,power=math.sin(t*math.pi),anim=anim)
    elif anim=="block": p=Pose(t,squat=3,arm_l=-35,arm_r=-42,staff=-52,veil=.1,power=.35+.15*wave,anim=anim)
    elif anim=="hit":
        k=math.sin(t*math.pi); p=Pose(t,x=-4*k,lean=-15*k,arm_l=28*k,arm_r=-26*k,staff=30,veil=.8,power=k,expression=1,anim=anim)
    elif anim=="death": p=Pose(t,y=11*t,lean=-82*min(1,t*1.25),arm_l=26,arm_r=-28,staff=70,veil=.85,expression=2,anim=anim)
    elif anim=="talk": p=Pose(t,y=wave*.5,arm_l=-18+8*wave,arm_r=13-5*wave,staff=-7,veil=.2,expression=3,anim=anim)
    elif anim=="interact":
        k=math.sin(t*math.pi); p=Pose(t,lean=4*k,arm_r=-48*k,arm_l=5,staff=-20,veil=.25,power=k,anim=anim)
    elif anim=="astrolabe_guard":
        k=math.sin(t*math.pi); p=Pose(t,squat=2*k,arm_l=-44*k,arm_r=-52*k,staff=-62*k,veil=.1,power=k,anim=anim)
    elif anim=="conic_lance":
        k=math.sin(t*math.pi); p=Pose(t,x=2*k,lean=14*k,arm_l=-20*k,arm_r=58*k,staff=72*k-18,veil=.7,power=k,anim=anim)
    elif anim=="epicycle_orbit":
        k=math.sin(t*math.pi); p=Pose(t,y=-2*k,arm_l=-34*k,arm_r=34*k,staff=-12+360*t,veil=.55,power=k,anim=anim)
    elif anim=="library_of_shadows":
        k=math.sin(t*math.pi); p=Pose(t,y=-1*k,arm_l=-50*k,arm_r=48*k,staff=-20,veil=.35,power=k,expression=4,anim=anim)
    elif anim=="missing_folio":
        k=math.sin(t*math.pi); p=Pose(t,arm_l=-42*k+8*wave,arm_r=38*k-8*wave,staff=-28,veil=.5,power=k,expression=5,anim=anim)
    elif anim=="prime_revelation":
        k=math.sin(t*math.pi); p=Pose(t,y=-4*k,arm_l=-58*k,arm_r=58*k,staff=-90*k,veil=.05,power=k,expression=6,anim=anim)
    elif anim=="celebrate": p=Pose(t,y=-3*abs(wave),arm_l=-55+8*wave,arm_r=48-8*wave,staff=-35,veil=.25,expression=3,anim=anim)
    elif anim=="taunt": p=Pose(t,arm_l=-5,arm_r=-22+10*wave,staff=-8,veil=.3,power=.45+.2*wave,expression=7,anim=anim)
    return p


def _draw_astrolabe(draw:ImageDraw.ImageDraw,cx:float,cy:float,r:float,angle:float,alpha:float=1.0)->None:
    c=_fade(BRONZE_LIGHT,alpha)
    _ellipse(draw,(cx-r,cy-r,cx+r,cy+r),(0,0,0,0),_fade(BRONZE,alpha),1.5)
    _ellipse(draw,(cx-r*.62,cy-r*.62,cx+r*.62,cy+r*.62),(0,0,0,0),c,1)
    a=math.radians(angle)
    _line(draw,[(cx-math.cos(a)*r*.9,cy-math.sin(a)*r*.9),(cx+math.cos(a)*r*.9,cy+math.sin(a)*r*.9)],c,1.2)
    _line(draw,[(cx-math.cos(a+1.57)*r*.8,cy-math.sin(a+1.57)*r*.8),(cx+math.cos(a+1.57)*r*.8,cy+math.sin(a+1.57)*r*.8)],_fade(c,.7),1)
    for i in range(7):
        aa=i/7*math.tau+a
        x=cx+math.cos(aa)*r*.78; y=cy+math.sin(aa)*r*.78
        _ellipse(draw,(x-1.2,y-1.2,x+1.2,y+1.2),_fade(STAR,alpha))


def _draw_folio(draw:ImageDraw.ImageDraw,cx:float,cy:float,angle:float,alpha:float=1.0,missing:bool=False)->None:
    w,h=13,17
    ca,sa=math.cos(angle),math.sin(angle)
    def tr(x:float,y:float)->Point: return (cx+x*ca-y*sa,cy+x*sa+y*ca)
    pts=[tr(-w/2,-h/2),tr(w/2,-h/2),tr(w/2,h/2),tr(-w/2,h/2)]
    _poly(draw,pts,_fade(PARCHMENT,alpha),_fade(OUTLINE,alpha),1)
    for yy in (-5,-1,3,7):
        if missing and yy==3: continue
        _line(draw,[tr(-4,yy),tr(4,yy)],_fade(INK,alpha*.7),.7)
    if missing:
        hole=[tr(-1,0),tr(5,0),tr(5,7),tr(0,7)]
        _poly(draw,hole,(0,0,0,0),_fade(CYAN,alpha*.7),.7)


def _draw_shadow(draw:ImageDraw.ImageDraw,cx:float,base:float,kind:int,color:RGBA,alpha:float)->None:
    c=_fade(color,alpha)
    _ellipse(draw,(cx-9,base-65,cx+9,base-47),c)
    if kind==0:
        _poly(draw,[(cx-13,base-47),(cx-18,base-5),(cx+17,base-5),(cx+12,base-47)],c)
        _line(draw,[(cx+11,base-40),(cx+25,base-12)],c,3)
    elif kind==1:
        _poly(draw,[(cx-15,base-45),(cx-20,base-4),(cx+19,base-4),(cx+14,base-45)],c)
        _ellipse(draw,(cx+9,base-51,cx+26,base-34),(0,0,0,0),c,2)
    else:
        _poly(draw,[(cx-16,base-46),(cx-12,base-4),(cx+17,base-4),(cx+14,base-46)],c)
        _poly(draw,[(cx-16,base-43),(cx-27,base-30),(cx-15,base-27)],c)


def _draw_effects_behind(draw:ImageDraw.ImageDraw,pose:Pose)->None:
    if pose.anim=="library_of_shadows":
        for i,(dx,c) in enumerate([(-28,SHADOW_A),(0,SHADOW_B),(28,SHADOW_C)]):
            alpha=.12+.42*pose.power*(.75+.25*math.sin(pose.phase*math.tau+i))
            _draw_shadow(draw,64+dx,112,i,c,alpha)
    elif pose.anim=="prime_revelation":
        _ellipse(draw,(24,7,104,87),_fade(INDIGO_LIGHT,.08+.16*pose.power),_fade(STAR,.35*pose.power),1)
        for i in range(11):
            a=i/11*math.tau+pose.phase
            r=34
            x=64+math.cos(a)*r; y=46+math.sin(a)*r
            _ellipse(draw,(x-1.3,y-1.3,x+1.3,y+1.3),_fade(STAR,.2+.8*pose.power))
        for i in range(0,11,2):
            a=i/11*math.tau+pose.phase
            b=((i*4+3)%11)/11*math.tau+pose.phase
            _line(draw,[(64+math.cos(a)*34,46+math.sin(a)*34),(64+math.cos(b)*34,46+math.sin(b)*34)],_fade(CYAN,.35*pose.power),.8)
    elif pose.anim=="epicycle_orbit":
        for i,r in enumerate((25,34,43)):
            _ellipse(draw,(64-r,49-r*.55,64+r,49+r*.55),(0,0,0,0),_fade(CYAN,.16+.22*pose.power),1)
            a=pose.phase*math.tau*(i+1)+i
            x=64+math.cos(a)*r; y=49+math.sin(a)*r*.55
            _ellipse(draw,(x-2,y-2,x+2,y+2),_fade([BRONZE_LIGHT,CYAN,STAR][i],.5+.5*pose.power))
    elif pose.anim=="missing_folio":
        for i in range(7):
            a=i/7*math.tau+pose.phase*2
            r=25+13*pose.power
            _draw_folio(draw,64+math.cos(a)*r,51+math.sin(a)*r*.65,a*.3,.25+.7*pose.power,missing=(i%3==0))


def _draw_character(draw:ImageDraw.ImageDraw,pose:Pose)->None:
    cx=63+pose.x; base=113+pose.y
    # legs and sandals
    for side,dx,step in [(-1,-9,pose.foot_l),(1,9,pose.foot_r)]:
        hip=(cx+dx,83+pose.y+pose.squat*.2)
        ankle=(cx+dx+step*.3,base-8)
        _capsule(draw,hip,ankle,4.6,SKIN_SHADE)
        _ellipse(draw,(ankle[0]-7,base-9,ankle[0]+8,base-2),BRONZE,OUTLINE,1)
    # mantle and armored body
    _poly(draw,[(cx-19,48+pose.y),(cx-25,101+pose.y),(cx+23,101+pose.y),(cx+18,48+pose.y)],MIDNIGHT,OUTLINE,2)
    _poly(draw,[(cx-22,58+pose.y),(cx-29,103+pose.y),(cx-4,94+pose.y),(cx,55+pose.y)],INDIGO,OUTLINE,1.5)
    _poly(draw,[(cx+19,58+pose.y),(cx+27,102+pose.y),(cx+2,94+pose.y),(cx,55+pose.y)],PURPLE,OUTLINE,1.5)
    _poly(draw,[(cx-15,52+pose.y),(cx-13,76+pose.y),(cx+14,76+pose.y),(cx+15,52+pose.y)],BRONZE,OUTLINE,1.2)
    for y in (57,64,71): _line(draw,[(cx-12,y+pose.y),(cx+12,y+pose.y)],BRONZE_LIGHT,1)
    # arms
    shoulder_y=57+pose.y
    wrists=[]
    for side,ang in [(-1,pose.arm_l),(1,pose.arm_r)]:
        shoulder=(cx+side*16,shoulder_y)
        rad=math.radians(90+side*12+ang)
        elbow=(shoulder[0]+math.cos(rad)*18,shoulder[1]+math.sin(rad)*18)
        wrist=(elbow[0]+math.cos(rad+side*.18)*16,elbow[1]+math.sin(rad+side*.18)*16)
        _capsule(draw,shoulder,elbow,5.2,INDIGO_LIGHT)
        _capsule(draw,elbow,wrist,4.3,SKIN)
        _ellipse(draw,(wrist[0]-4,wrist[1]-4,wrist[0]+4,wrist[1]+4),SKIN_LIGHT,OUTLINE,1)
        wrists.append(wrist)
    # head, hood, veil; the astrolabe reads as a halo behind the face rather
    # than a mask laid over it.
    hx=cx+pose.lean*.12; hy=31+pose.y+pose.squat*.12
    _draw_astrolabe(draw,hx,hy-1,20,pose.phase*45+pose.staff*.2,.82)
    _ellipse(draw,(hx-14,hy-17,hx+14,hy+17),HAIR,OUTLINE,1.5)
    _ellipse(draw,(hx-10,hy-12,hx+10,hy+12),SKIN,OUTLINE,1)
    _poly(draw,[(hx-16,hy-9),(hx-12,hy-20),(hx+12,hy-20),(hx+17,hy-8),(hx+12,hy+2),(hx-12,hy+2)],MIDNIGHT,OUTLINE,1.5)
    # eyes, deliberately partially hidden
    _line(draw,[(hx-7,hy-2),(hx-1,hy-3)],OUTLINE,1.5)
    _line(draw,[(hx+2,hy-3),(hx+8,hy-2)],OUTLINE,1.5)
    _ellipse(draw,(hx-5,hy-2,hx-3,hy),CYAN)
    _ellipse(draw,(hx+4,hy-2,hx+6,hy),CYAN)
    veil_alpha=.72
    _poly(draw,[(hx-12,hy+1),(hx+12,hy),(hx+9,hy+15),(hx-9,hy+14)],_fade(INDIGO_LIGHT,veil_alpha),_fade(OUTLINE_SOFT,.8),.7)
    for i in range(3): _line(draw,[(hx-8+i*5,hy+3),(hx-6+i*5,hy+12)],_fade(CYAN,.22),.5)
    # staff in right hand, with armillary head
    hand=wrists[1]
    angle=math.radians(-62+pose.staff)
    tip=(hand[0]+math.cos(angle)*48,hand[1]+math.sin(angle)*48)
    butt=(hand[0]-math.cos(angle)*26,hand[1]-math.sin(angle)*26)
    _line(draw,[butt,tip],OUTLINE,4)
    _line(draw,[butt,tip],BRONZE_LIGHT,2)
    _draw_astrolabe(draw,tip[0],tip[1],8,pose.phase*180+pose.staff,1)
    # left hand holds fragment during idle/talk
    if pose.anim in {"idle","talk","taunt"}:
        _draw_folio(draw,wrists[0][0]-2,wrists[0][1]-4,-.15,.9,missing=True)


def _draw_effects_front(draw:ImageDraw.ImageDraw,pose:Pose)->None:
    if pose.anim in {"astrolabe_guard","block"}:
        _draw_astrolabe(draw,83,58,19,pose.phase*240,.45+.55*pose.power)
        _ellipse(draw,(63,38,103,78),_fade(CYAN,.05+.1*pose.power),_fade(CYAN,.35*pose.power),1)
    elif pose.anim=="conic_lance":
        # three conic traces converge toward the staff strike
        _arc(draw,(66,21,128,91),105,255,_fade(CYAN,.35+.6*pose.power),2)
        _arc(draw,(73,30,127,78),135,225,_fade(BRONZE_LIGHT,.35+.6*pose.power),2)
        _line(draw,[(82,69),(126,50)],_fade(STAR,.4+.6*pose.power),2.5)
    elif pose.anim=="library_of_shadows":
        for x,c in [(35,SHADOW_A),(64,SHADOW_B),(93,SHADOW_C)]:
            _line(draw,[(x,93),(64,71)],_fade(c,.35*pose.power),1.2)
    elif pose.anim=="missing_folio":
        _poly(draw,[(100,28),(118,35),(112,54),(94,47)],_fade(PARCHMENT,.5+.5*pose.power),_fade(OUTLINE,.8),1)
        _poly(draw,[(105,39),(118,35),(112,54)],(0,0,0,0),_fade(CYAN,.8),1)
    elif pose.anim=="prime_revelation":
        _draw_astrolabe(draw,64,46,31,pose.phase*120,pose.power)
        _line(draw,[(64,15),(64,78)],_fade(STAR,.5*pose.power),1)
        _line(draw,[(34,46),(94,46)],_fade(STAR,.5*pose.power),1)
    elif pose.anim=="taunt":
        # two incompatible portrait fragments hover beside her
        _draw_folio(draw,100,31,-.2,.65,missing=False)
        _draw_folio(draw,105,50,.2,.65,missing=True)
        _line(draw,[(96,24),(112,57)],_fade(SHADOW_B,.6),1.5)


def render_frame(anim:str,frame_idx:int,nframes:int)->Image.Image:
    pose=_pose(anim,frame_idx,nframes)
    behind=Image.new("RGBA",(FRAME_W*SUPER,FRAME_H*SUPER),(0,0,0,0))
    body=Image.new("RGBA",behind.size,(0,0,0,0))
    front=Image.new("RGBA",behind.size,(0,0,0,0))
    _draw_effects_behind(blending_draw(behind),pose)
    _draw_character(blending_draw(body),pose)
    _draw_effects_front(blending_draw(front),pose)
    image=Image.alpha_composite(Image.alpha_composite(behind,body),front)
    return image.resize((FRAME_W,FRAME_H),Image.Resampling.LANCZOS)


def _render_native_portrait(expression:str="default",phase:float=0.0)->Image.Image:
    anim={"default":"idle","talk":"talk","shadow":"library_of_shadows","folio":"missing_folio","reveal":"prime_revelation"}.get(expression,"idle")
    n=12 if anim in {"library_of_shadows","prime_revelation"} else 10 if anim=="missing_folio" else 8
    frame=render_frame(anim,int(phase*n)%n,n)
    return frame.crop((25,1,103,79)).resize(PORTRAIT_SIZE,Image.Resampling.LANCZOS)


def render_portraits(out_dir:Path,**opts)->List[Path]:
    del opts
    clips={
        "default":PortraitClip.still(_render_native_portrait("default")),
        "talk":PortraitClip(tuple(_render_native_portrait("talk",i/8) for i in range(8)),duration_ms=104,looping=True),
        "shadow":PortraitClip(tuple(_render_native_portrait("shadow",i/8) for i in range(8)),duration_ms=90,looping=True),
        "folio":PortraitClip.still(_render_native_portrait("folio",.45)),
        "reveal":PortraitClip.still(_render_native_portrait("reveal",.5)),
    }
    return write_portrait_sheet(TARGET_NAME,clips,Path(out_dir))


def _body_metrics_override(fw:int,fh:int):
    return {
        "body_pixel_bbox":{"x":int(fw*.22),"y":int(fh*.03),"w":int(fw*.63),"h":int(fh*.89)},
        "feet_pixel":{"x":fw*.5,"y":fh*.91},
        "feet_anchor_norm":{"x":0.0,"y":round(.5-.91,6)},
    }


def render(out_dir:Path,**opts)->List[Path]:
    del opts
    outputs=build_sheet(
        target=TARGET_NAME,rows=ROWS,render_fn=render_frame,out_dir=Path(out_dir),
        frame_size=(FRAME_W,FRAME_H),label_width=112,auto_crop=False,
        body_metrics_fn=_body_metrics_override,actor_metadata=ACTOR_METADATA,
        sheet_tuning={"collision_scale":1.0,"frame_sample_inset":1},
        animation_key_map={name:name for name,_frames,_duration in ROWS},trim=False,
        attack_hitboxes={
            "conic_lance":{"bbox":{"x":68,"y":18,"w":60,"h":79}},
            "epicycle_orbit":{"bbox":{"x":18,"y":12,"w":108,"h":83}},
            "library_of_shadows":{"bbox":{"x":14,"y":11,"w":112,"h":96}},
            "missing_folio":{"bbox":{"x":20,"y":8,"w":108,"h":92}},
            "prime_revelation":{"bbox":{"x":22,"y":6,"w":84,"h":85}},
        },
    )
    keys=("spritesheet","yaml","ron","actor","canonical","canonical_transparent","preview")
    return [Path(outputs[key]) for key in keys if outputs.get(key)]


def render_canonical(out_dir:Path,**opts)->Path:
    del opts
    return write_canonical(TARGET_NAME,ROWS,render_frame,Path(out_dir),frame_size=(FRAME_W,FRAME_H))


__all__=["ACTOR_METADATA","AUTHORING_DESCRIPTION","TARGET_NAME","render","render_canonical","render_frame","render_portraits"]

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out_dir",nargs="?",type=Path,default=Path("generated")/TARGET_NAME)
    args=parser.parse_args()
    for path in render(args.out_dir): print(path)
    for path in render_portraits(args.out_dir): print(path)
