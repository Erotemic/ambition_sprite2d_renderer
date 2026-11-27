"""The Reader, a Math Town resident who reads during weight training.

The book and weight are parts of the art for the exercise routine, not
inventory items. The idle row is a full curl. The reader holds the book
steady while the free arm moves the weight. The feet stay on the ground.
"""
from __future__ import annotations

import math
from pathlib import Path

from ...authoring.sheet_build import build_sheet
from ...core.draw import rotate_transparent_sprite
from ...core.measure import body_metrics_for_box
from ._clockwork_enemy_art import Canvas, add, bezier, mix, mul, perp, rot, sub, unit

TARGET_NAME = "exercise_reader"
FRAME_SIZE = (224, 208)
GROUND = 190
ROWS = [
    ("idle", 24, 100),
    ("walk", 12, 100),
    ("run", 12, 70),
    ("talk", 8, 110),
    ("hurt", 6, 85),
    ("death", 10, 100),
]

ACTOR_METADATA = {
    "actor": {"character_id": "npc_exercise_reader", "display_name": "The Reader"},
    "body": {
        "body_plan": "HumanoidBiped", "body_kind": "Standard", "mass_class": "Medium",
        "locomotion_hint": "Walk", "traits": ["humanoid", "math_town", "reader", "athlete"],
    },
    "capabilities": {
        "traversal": {"walk": True, "use_lifts": True, "door_access": ["public"]},
        "interactions": {"talk": True, "open_doors": ["public"]},
    },
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "peaceful"},
    "visual": {
        "default_pose": "idle",
        "portrait": {"face_guide": {
            "center": {"x": 111.0, "y": 44.0},
            "size": {"width": 50.0, "height": 62.0},
            "source_size": {"width": FRAME_SIZE[0], "height": FRAME_SIZE[1]},
        }},
    },
    "tags": ["humanoid", "math_town", "reader", "athlete"],
    "animation_bindings": {
        key: {"animation": row, "events": []}
        for key, row in (
            ("default", "idle"), ("locomotion.walk", "walk"),
            ("locomotion.run", "run"), ("interaction.talk", "talk"),
            ("damage.hit", "hurt"), ("damage.death", "death"),
        )
    },
    "authoring_description": "An athletic resident of Math Town. The Reader studies a mathematics book while doing one-arm dumbbell curls.",
    "dialogue_hints": {"barks": ["I have two sets left.", "Left as an exercise to the reader."]},
}

INK = "#292c38"
SKIN, SKIN_L, SKIN_D = "#c98960", "#eab187", "#9c5947"
FAR_SKIN = "#ae6a51"
HAIR, HAIR_L = "#382c35", "#65505a"
TEAL, TEAL_L, TEAL_D = "#327d83", "#65b9ae", "#24535e"
SHORTS, SHORTS_L, SHORTS_D = "#3e465c", "#59657b", "#2b3245"
RED, RED_L = "#c6574c", "#e98a71"
CREAM, SOLE = "#f2e8d3", "#bbb8ad"
METAL, METAL_L, METAL_D = "#727c86", "#c3cbd0", "#414952"
BOOK, PAGE, PAGE_D = "#a04e3b", "#fff0cb", "#ded0ae"


def limb(d, a, b, r0, r1, color, light, shade):
    """Draw a tapered limb with a rounded contour and attached shading."""
    axis = unit(sub(b, a))
    n = perp(axis)
    p = lambda t, r: add(mix(a, b, t), mul(n, r))
    pts = bezier(p(0, r0), p(.25, r0 * 1.2), p(.7, r1 * 1.12), p(1, r1))
    pts += [add(b, rot(mul(n, r1), -180 * i / 12)) for i in range(1, 13)]
    pts += bezier(p(1, -r1), p(.65, -r1), p(.3, -r0 * 1.1), p(0, -r0))[1:]
    pts += [add(a, rot(mul(n, -r0), -180 * i / 12)) for i in range(1, 13)]
    d.poly(pts, color, INK, 1.8)
    d.line([p(.12, -r0 * .47), p(.43, -r0 * .62), p(.78, -r1 * .5)], light, 2.2)
    d.line([p(.36, r0 * .62), p(.68, r1 * .7), p(.9, r1 * .48)], shade, 1.6)


def shoe(d, x, y, far=False):
    # y is the bottom of the sole.
    pts = [(x-9,y-13),(x+5,y-14),(x+10,y-8),(x+22,y-7),(x+25,y-3),
           (x+23,y),(x-11,y),(x-13,y-4)]
    d.poly(pts, SOLE if far else CREAM, INK, 1.8)
    d.poly([(x-12,y-4),(x+24,y-4),(x+23,y),(x-11,y)], METAL_D, INK, 1.1)
    d.poly([(x-9,y-12),(x-3,y-13),(x-1,y-6),(x-9,y-6)], TEAL_D if far else TEAL, None)
    for k in range(3):
        d.line([(x+2+k*4,y-10+k),(x+5+k*4,y-7+k*.3)], INK, 1)


def leg(d, hip, knee, ankle, far=False):
    skin = FAR_SKIN if far else SKIN
    limb(d, hip, knee, 12, 9, SHORTS_D if far else SHORTS, SHORTS_L, SHORTS_D)
    limb(d, knee, ankle, 8.5, 5.5, skin, SKIN_L, SKIN_D)
    cuff = mix(knee, ankle, .74)
    limb(d, cuff, ankle, 6, 5.5, SOLE if far else CREAM, CREAM, SOLE)
    d.line([add(cuff, (-5, 3)), add(cuff, (5, 3))], TEAL, 1.8)
    shoe(d, ankle[0], ankle[1]+8, far)


def weight(d, center, angle):
    """Draw both ends of a hex dumbbell on the same grip axis."""
    p = lambda x, y: add(center, rot((x, y), angle))
    d.line([p(-21, 0), p(21, 0)], INK, 8)
    d.line([p(-19, -1), p(19, -1)], METAL_L, 4)
    for x in (-22, 22):
        poly = [(x-7,-10),(x+5,-12),(x+10,-6),(x+10,7),(x+4,12),(x-8,10),(x-10,5),(x-10,-5)]
        d.poly([p(*a) for a in poly], METAL_D, INK, 1.9)
        d.poly([p(x-6,-8),p(x+4,-10),p(x+7,-5),p(x+3,-1),p(x-7,-2)], METAL, None)
        d.line([p(x-6,-8),p(x+4,-10)], METAL_L, 1.5)


def book(d, center, page_turn=0.):
    p = lambda x, y: add(center, (x, y))
    # Cover, page blocks, then the two open faces.
    d.poly([p(-27,-19),p(-4,-13),p(26,-24),p(30,11),p(0,23),p(-30,13)], BOOK, INK, 2)
    d.poly([p(-26,-19),p(-3,-11),p(25,-22),p(27,8),p(0,19),p(-27,10)], PAGE_D, INK, 1.1)
    d.poly([p(-25,-23),p(-2,-16),p(0,17),p(-27,6)], PAGE, INK, 1.2)
    d.poly([p(-2,-16),p(25,-26),p(27,5),p(0,17)], CREAM, INK, 1.2)
    d.line([p(-2,-16),p(0,17)], BOOK, 1.4)
    # A triangle and ruled equations read as a textbook without tiny text.
    d.line([p(-19,-15),p(-7,-10),p(-9,1),p(-19,-15)], TEAL_D, 1.2)
    for y in (4,8):
        d.line([p(-22,y-2),p(-7,y+2)], METAL, .9)
    for y in (-15,-10,-5,0,5):
        d.line([p(5,y+2),p(20,y-4)], METAL, .9)
    if page_turn > 0:
        d.poly([p(0,17),p(-2,-16),p(-2-18*page_turn,-30-6*page_turn),p(-8-15*page_turn,5)], PAGE, INK, 1.1)
    # Bookmark below the binding.
    d.poly([p(3,19),p(7,18),p(8,29),p(5,26),p(3,29)], RED, INK, .7)


def _render_frame(animation, i, n):
    loop = animation in ("idle", "walk", "run", "talk")
    t = i / max(1, n if loop else n-1)
    a = math.tau * t
    stride = 1 if animation == "walk" else 1.55 if animation == "run" else 0
    bob = -2*abs(math.sin(a))*stride + .55*math.sin(a)
    recoil = math.sin(math.pi*t) if animation == "hurt" else 0.
    # The canonical frame begins near the top of a curl.
    curl = .5 + .5*math.cos(a) if animation == "idle" else .35 if stride else .60
    d = Canvas(FRAME_SIZE)
    B = lambda x, y: (x-7*recoil, y+bob)
    hip_y = 130 + bob
    for far, side in ((True, 1), (False, -1)):
        ph = a + (math.pi if far else 0)
        base_x = 110 + side*11
        step = math.sin(ph)*19*stride
        lift = max(0, math.cos(ph))*14*stride
        leg(d, (base_x,hip_y), (base_x+step*.52,157-lift*.33),
            (base_x+step,GROUND-8-lift), far)
    # Far arm supports the book. It sits behind the torso.
    sh, el, hand = B(129,83), B(147,112), B(153,94)
    limb(d, sh, el, 10, 7.5, FAR_SKIN, SKIN_L, SKIN_D)
    limb(d, el, hand, 8, 5.8, FAR_SKIN, SKIN_L, SKIN_D)
    d.disk(hand, 6.5, FAR_SKIN, INK, 1.4)
    # Neck, athletic singlet, waistband and side seam.
    d.box(B(112,67), 10, 12, SKIN_D, INK, 1.4, 5)
    outline = [(90,72),(102,70),(112,77),(126,70),(134,81),(132,96),
               (124,115),(126,130),(91,130),(86,115),(83,92),(83,82)]
    d.poly([B(*p) for p in outline], TEAL, INK, 2)
    d.poly([B(*p) for p in [(83,82),(92,77),(99,96),(94,118),(98,128),(91,130),(86,115),(83,92)]], TEAL_D, None)
    d.line([B(102,73), B(112,80), B(125,73)], CREAM, 2.7)
    d.line([B(89,78), B(94,88), B(94,97)], TEAL_L, 2.1)
    d.line([B(132,82), B(128,100), B(122,119)], TEAL_L, 2)
    d.poly([B(*p) for p in [(91,124),(126,124),(128,132),(90,132)]], SHORTS, INK, 1.6)
    d.line([B(105,127),B(109,132),B(113,127)], CREAM, 1.2)
    # Head, with the eyes directed down toward the page.
    d.oval(B(111,47), 21, 24, SKIN, INK, 2, 7)
    d.oval(B(94,51), 6, 8, SKIN_D, INK, 1.4, -12)
    d.line([B(94,48), B(96,53)], SKIN_L, 1.7)
    d.poly([B(*p) for p in [(124,47),(135,55),(126,59),(124,56)]], SKIN_L, INK, 1.3)
    d.line([B(118,64), B(125,64), B(127,62)], INK, 1.4)
    if animation == "talk" and i % 4 in (1,2):
        d.oval(B(123,64), 4, 2.4, SKIN_D, INK, 1)
    # Curly hair and terrycloth headband.
    for x,y,r in [(92,34,9),(99,27,10),(109,25,11),(120,28,10),(128,34,8)]:
        d.disk(B(x,y),r,HAIR,INK,1.1)
    d.line([B(100,25),B(109,21),B(119,25)],HAIR_L,1.8)
    d.poly([B(*p) for p in [(91,34),(100,37),(118,38),(132,34),(132,42),(119,46),(100,45),(91,42)]],RED,INK,1.5)
    d.line([B(94,37),B(114,41),B(129,37)],RED_L,1.5)
    # Rectangular reading glasses and visible pupils.
    for x,y,rx in [(108,51,7.5),(126,50,5.7)]:
        d.box(B(x,y),rx,6,SKIN_L,INK,1.8,2.2,6)
        if (animation == "idle" and i in (13,14)) or recoil > .8:
            d.line([B(x-3,y+1),B(x+3,y+1)], INK,1.3)
        else:
            d.disk(B(x+2,y+2),2,INK,None)
        d.line([B(x-rx+2,y-3),B(x-rx+5,y-3)],CREAM,1.3)
    d.line([B(115,50), B(120,50)],INK,1.8)
    d.line([B(96,47), B(100,48)],INK,1.6)
    # Near arm performs the curl. The elbow remains near the hip.
    sh, el = B(86,85), B(74,116)
    theta = math.radians(65 + 150*curl)
    # At the low end the forearm points down; at the high end it points up.
    grip = add(el, (33*math.cos(theta), 33*math.sin(theta)))
    limb(d, sh, el, 12, 8, SKIN, SKIN_L, SKIN_D)
    limb(d, el, grip, 9, 5.8, SKIN, SKIN_L, SKIN_D)
    d.box(mix(el,grip,.87), 6.5, 5, RED, INK, 1.1, 2, math.degrees(theta)-90)
    weight(d, grip, 10-16*curl)
    d.oval(grip, 7.5, 7, SKIN_L, INK, 1.7, 8)
    for k in range(3):
        d.line([add(grip,(-4+k*3,1)),add(grip,(-3+k*3,4))],SKIN_D,.9)
    # The pages face the reader but remain visible to the player.
    turn = math.sin(math.pi*(i-17)/5) if animation == "idle" and 17<i<22 else 0.
    book(d, B(156,94), turn)
    d.oval(B(152,113), 6.8, 5.5, SKIN_L, INK, 1.4, -18)
    image = d.finish()
    if animation == "death":
        angle = -88 * min(1, t*1.3)
        tilted = rotate_transparent_sprite(image, angle, expand=True)
        bb = tilted.getchannel("A").getbbox()
        if bb:
            from PIL import Image
            art = tilted.crop(bb)
            image = Image.new("RGBA", FRAME_SIZE)
            image.paste(art, ((FRAME_SIZE[0]-art.width)//2, GROUND-art.height+1))
    return image


def _body_metrics(fw, fh):
    # Exclude the book and weight from the upright body box.
    return body_metrics_for_box((83, 15, 137, GROUND+1), fw, fh)


def render(out_dir: str | Path, **opts):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        target=TARGET_NAME, rows=ROWS, render_fn=_render_frame,
        out_dir=out_dir, frame_size=FRAME_SIZE, auto_crop=False,
        actor_metadata=ACTOR_METADATA, body_metrics_fn=_body_metrics,
        pose_bodies="authored",
    )
    return [outputs[k] for k in ("spritesheet", "yaml", "ron", "actor", "preview", "canonical", "canonical_transparent")]
