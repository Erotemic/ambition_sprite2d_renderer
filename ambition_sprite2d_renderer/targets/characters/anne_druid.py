"""Sprite generator for Anne Druid: the keeper of the message we sent to
whoever is out there.

An affectionate science-fantasy parody of Ann Druyan, who chose what went on
the Voyager Golden Record. She is not a portrait: she is a cosmic naturalist,
part druid of a forest and part archivist of a spacecraft.

The look (2026-10-13): a druid of a high fantasy, seen three quarters from
the front, facing right: a woman of sixty or so who stands easily and smiles
easily. Long dark hair with silver in it, loose down her back, and on it a
circlet of leaves with two small antlers. A moss-green robe to her ankles
whose hem is cut like leaves, a leather belt with a gold disc for its buckle
(the record), vines wound on her forearms, and a cloak of forest green over
her shoulders: its lining is the night sky. Her staff is a gnarled branch
with a pale stone in its fork; at rest it is across her back, and in the rows
that are its own it is in her hand.

Jon, 2026-10-13, of the draft before this one (a teal coat with a star map on
it, and a scarf): "Anne Druid needs to read as a high fantasy druid."

She is drawn as herself, not as one shape that every woman of the cast
shares (Jon, 2026-10-13: "The women need to read more as women, and there
needs to be variation"). She is a grown woman, not a mascot. There is no drop
shadow.

What she shows: the record; a whale's song; the map of the pulsars that says
where home is; a garden that comes up out of the ground with stars in it.

She is a person of ``_person_rig``: the bones, the poses and the frame are
shared; the head, the clothes, how she stands and what she shows are hers.
Her dialogue portraits are frames of this sheet (``Person.portraits``).
"""

from __future__ import annotations

import math
from typing import List

from ._ai_era_kit import OUTLINE, WHITE, RGBA, lerp, mix, pin
from . import _person_rig as R
from ._person_rig import Build, Person, Stamp, loop, shot

TARGET_NAME = "anne_druid"
DISPLAY_NAME = "Anne Druid"

AUTHORING_DESCRIPTION = {
    "parody_of": "Ann Druyan",
    "concept": (
        "An affectionate science-fantasy transformation of the writer, producer, "
        "science communicator, and Voyager Golden Record creative director into "
        "a cosmic druid who preserves messages for distant life."
    ),
    "name_origin": (
        "Anne Druid turns Ann Druyan's surname into a fantasy class while keeping "
        "the character centered on communication, wonder, skepticism, and cosmic scale."
    ),
    "visual_inspiration": [
        "The Voyager Golden Record becomes a luminous circular shield and spell focus.",
        "The pulsar map becomes branching silver-gold line work around major casts.",
        "Whale song and natural sounds become expanding cyan waveform rings.",
        "A teal travelling robe and constellation vines merge naturalist and cosmic imagery.",
        "Dark hair with silver star-like streaks creates a mature, specific silhouette without copying a photograph.",
    ],
    "gameplay_inspiration": [
        "golden_record_guard blocks and reflects with the record's engraved surface.",
        "whale_song converts recorded natural sound into a broad resonant wave.",
        "pulsar_beacon marks space with a rotating astronomical navigation diagram.",
        "cosmic_garden grows orbiting seeds and constellation vines from the floor.",
        "voyager_cast sends the record outward and recalls it like an interstellar boomerang."
    ],
    "boundaries": [
        "Treat the character as a warm fictional homage, not a literal likeness or biographical claim.",
        "Preserve agency and scientific curiosity; do not reduce her to somebody else's companion.",
        "Keep the Golden Record, natural sound, and cosmic communication as the central design language.",
        "Avoid generic witch iconography when a scientific or naturalist visual metaphor can do the same job.",
    ],
}

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 148),
    ("walk", 8, 104),
    ("run", 8, 80),
    ("crouch", 6, 96),
    ("crouch_walk", 8, 92),
    ("jump", 6, 90),
    ("fall", 6, 92),
    ("land_hard", 7, 84),
    ("dash_startup", 4, 54),
    ("dash", 6, 60),
    ("slide", 6, 68),
    ("roll", 8, 62),
    ("wall_grab", 6, 104),
    ("wall_jump", 6, 82),
    ("ledge_grab", 6, 98),
    ("ledge_climb", 6, 94),
    ("climb", 8, 98),
    ("swim", 8, 104),
    ("block", 6, 82),
    ("hit", 5, 84),
    ("death", 8, 108),
    ("talk", 8, 106),
    ("interact", 8, 94),
    ("golden_record_guard", 8, 68),
    ("whale_song", 10, 74),
    ("pulsar_beacon", 10, 76),
    ("cosmic_garden", 10, 78),
    ("voyager_cast", 10, 66),
    ("celebrate", 8, 90),
    ("taunt", 8, 96),
]

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_anne_druid",
        "display_name": "Anne Druid",
    },
    "authoring_description": AUTHORING_DESCRIPTION,
    "dialogue_hints": {
        "suggested_barks": [
            'The record is not a time capsule. It is an introduction.',
            'Listen long enough and the universe stops sounding empty.',
            'Wonder without skepticism is fog.',
            'The map points home. If you can read a pulsar.',
        ],
        "fallback_dialogue": [
            'We sent music, greetings, a heartbeat, and the sound of a kiss. Optimism is sometimes an engineering decision.',
            'A message for strangers begins with the hope that strangers can understand.',
            'Skepticism without wonder is a locked door.',
            'I do not know who finds it. That was never the point of sending it.',
        ],
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": [
            "story",
            "humanoid",
            "scientist",
            "science_communicator",
            "cosmic_druid",
            "golden_record_keeper",
            "playable_candidate",
        ],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": True,
            "climb": True,
            "fly": None,
            "swim": True,
            "crawl": True,
            "use_lifts": True,
            "door_access": ["public"],
        },
        "interactions": {
            "talk": True,
            "trade": None,
            "carry": None,
            "open_doors": ["public"],
        },
    },
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "peaceful"},
    "visual": {
        "default_pose": "idle",
        "portrait": {
            "face_guide": {
                "center": {"x": 65.0, "y": 31.0},
                "size": {"w": 31.0, "h": 35.0},
                "source_size": {"w": 128.0, "h": 128.0},
            }
        },
    },
    "tags": [
        "story",
        "humanoid",
        "scientist",
        "science_communicator",
        "cosmic_druid",
        "golden_record_keeper",
        "playable_candidate",
    ],
    "sockets": {
        "head": {"source": "explicit.anne_druid", "point": {"x": 65.0, "y": 30.0}},
        "chest": {"source": "explicit.anne_druid", "point": {"x": 64.0, "y": 62.0}},
        "hand_l": {"source": "explicit.anne_druid", "point": {"x": 46.0, "y": 73.0}},
        "hand_r": {"source": "explicit.anne_druid", "point": {"x": 84.0, "y": 70.0}},
        "record_center": {"source": "explicit.anne_druid", "point": {"x": 48.0, "y": 62.0}},
        "speech_bubble": {"source": "explicit.anne_druid", "point": {"x": 65.0, "y": 4.0}},
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "action.melee.primary": {"animation": "golden_record_guard", "events": []},
        "action.ranged.primary": {"animation": "voyager_cast", "events": []},
        "action.special.primary": {"animation": "whale_song", "events": []},
        "action.special.secondary": {"animation": "pulsar_beacon", "events": []},
        "action.special.tertiary": {"animation": "cosmic_garden", "events": []},
        "action.defense.block": {"animation": "block", "events": []},
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
                "revision_id": "anne_druid_concept_direction",
                "creator_kind": "human",
                "creator": "Jon Crall",
                "contribution": "selected_anne_druid_and_required_authoring_description_for_new_characters",
            },
            {
                "revision_id": "anne_druid_procedural_sprite_v1",
                "creator_kind": "model",
                "creator": "gpt-5.6-thinking",
                "parent_revision_id": "anne_druid_concept_direction",
                "contribution": "procedural_full_action_sprite_native_portraits_and_actor_authoring_notes",
            },
        ],
    },
}

# Palette: deep space and forest colors, with the record acting as the single
# high-value metallic focal point.
COAT: RGBA = (96, 138, 82, 255)
COAT_DARK: RGBA = (58, 94, 62, 255)
COAT_LIGHT: RGBA = (160, 192, 116, 255)
SCARF: RGBA = (124, 86, 58, 255)
SCARF_DARK: RGBA = (78, 52, 40, 255)
CLOAK: RGBA = (40, 76, 64, 255)
CLOAK_DARK: RGBA = (24, 50, 48, 255)
NIGHT: RGBA = (44, 46, 92, 255)
ANTLER: RGBA = (232, 214, 178, 255)
ANTLER_DARK: RGBA = (166, 140, 108, 255)
WOOD: RGBA = (130, 92, 62, 255)
WOOD_DARK: RGBA = (80, 54, 42, 255)
STONE: RGBA = (200, 240, 250, 255)
TROUSER: RGBA = (48, 50, 70, 255)
TROUSER_DARK: RGBA = (30, 32, 50, 255)
BOOT: RGBA = (96, 70, 56, 255)
BOOT_DARK: RGBA = (56, 40, 36, 255)
SKIN: RGBA = (228, 184, 150, 255)
SKIN_SHADE: RGBA = (194, 146, 120, 255)
SKIN_DEEP: RGBA = (146, 98, 88, 255)
HAIR: RGBA = (50, 44, 54, 255)
HAIR_LIGHT: RGBA = (200, 204, 216, 255)
INK: RGBA = (26, 22, 30, 255)
GOLD: RGBA = (250, 214, 110, 255)
GOLD_DARK: RGBA = (196, 132, 52, 255)
GOLD_PALE: RGBA = (255, 244, 196, 255)
SONG: RGBA = (150, 214, 250, 255)
SONG_DARK: RGBA = (60, 116, 190, 255)
LEAF: RGBA = (140, 214, 110, 255)
LEAF_DARK: RGBA = (56, 128, 72, 255)

#: 165 cm, easy in how she stands.
BUILD = Build(hip_up=47.0, thigh=22.9, shin=21.3, neck=(0.6, -35.0), upper=18.4, fore=17.4, near_shoulder=(-4.6, -30.8), far_shoulder=(5.6, -30.4),
              near_hip=(-3.8, 0.0), far_hip=(3.8, 0.0), head_up=(1.0, -12.2), height=106.0, half_width=(12.5, 13.5))

X = Person(TARGET_NAME, BUILD)
K = X.K
P = X.P
TOP = BUILD.neck[1] - 2.0
FRAME_W, FRAME_H = X.frame


def _front(d, hb: float, hf: float) -> None:
    """The neck of her robe, her belt with its gold disc, the folds of the
    skirt, and the hem, cut like leaves."""
    K.poly(d, [K.at(0.6, TOP - 1.0), K.at(8.0, TOP - 1.0), K.at(4.6, TOP + 8.0)], SKIN_SHADE)
    K.line(d, [K.at(0.6, TOP - 1.0), K.at(4.6, TOP + 8.0), K.at(8.0, TOP - 1.0)], COAT_LIGHT, 1.0)
    # Her bust: the robe is light on it and in shade under it.
    by = TOP + 12.5
    K.oval(d, K.at(6.4, by + 0.4), 2.8, 2.0, mix(COAT, COAT_LIGHT, 0.45))
    K.poly(d, [K.at(0.6, by + 3.4), K.at(4.6, by + 5.0), K.at(10.6, by + 3.6), K.at(9.4, by + 6.6), K.at(4.4, by + 7.4), K.at(0.6, by + 5.2)], COAT_DARK)
    K.poly(d, [K.at(-9.0, -14.4), K.at(9.4, -13.6), K.at(9.4, -10.8), K.at(-9.0, -11.6)], SCARF)
    K.oval(d, K.at(4.0, -12.4), 2.6, 2.6, GOLD, OUTLINE, 0.5)
    K.oval(d, K.at(4.0, -12.4), 1.4, 1.4, None, GOLD_DARK, 0.5)  # type: ignore[arg-type]
    K.poly(d, [K.at(1.6, -10.0), K.at(3.6, -10.0), K.at(3.0, 2.0), K.at(1.2, 1.4)], SCARF)
    for x in (-5.6, -0.6, 4.4, 8.0):
        K.line(d, [K.at(x * 0.8, -9.0), K.at(x * 1.5 - hb * 0.3 + hf * 0.2, 36.0)], COAT_DARK, 0.6)
    # The hem: a row of leaf points, the lighter green of new growth.
    for k in range(-6, 8):
        x = k * 3.6
        K.poly(d, [K.at(x - 1.8, 33.0), K.at(x + 1.8, 33.0), K.at(x, 39.6)], COAT_LIGHT)
    K.poly(d, [K.at(-30.0, 39.4), K.at(30.0, 39.4), K.at(30.0, 46.0), K.at(-30.0, 46.0)], COAT_DARK)


X.torso = R.make_figure(K, ("anne",), COAT, COAT_DARK, back=(7.4, 7.6, 6.4, 8.4, 11.6), front=(6.4, 10.6, 6.4, 8.8, 11.2), hem_y=BUILD.hip_up - 5.0, top=TOP,
                        shoulders=((-4.6, -30.2), (3.8, -30.2)), shoulder_r=(4.6, 3.6), shade_from=7.6, detail=_front)


def _mane(ctx) -> List[Stamp]:
    """Her hair down her back: it hangs in the world."""
    a = math.radians(ctx.turn)
    root = (ctx.head[0] - 6.4 * math.cos(a) - 1.0 * math.sin(a), ctx.head[1] - 6.4 * math.sin(a) + 1.0 * math.cos(a))
    at = pin(root)
    moving = ctx.anim in ("walk", "run", "dash", "fall", "jump")
    heading = 100.0 if not moving else 140.0 if ctx.anim != "fall" else 250.0
    links = max(2, min(6, int((ctx.ground - 4.0 - root[1]) / 4.6)))
    chains = [R.chain((root[0] - at[0] + dx, root[1] - at[1]), links, 4.6, heading + spread, wave=8.0 if moving else 3.0, curl=-3.0, phase=ctx.phase, lead=lead)
              for dx, spread, lead in ((0.0, 0.0, 0.0), (2.6, -10.0, 1.4))]
    return [(R.ribbon(K, ("anne_mane",), chains, 5.4, HAIR, HAIR_LIGHT, taper=0.45), at, "mane", 0.0)]


def _staff(length: int = 62):
    """Her staff, along +x from its foot: a gnarled branch, and a pale stone
    held in the fork at its head."""
    n = float(length)

    def shape(d) -> None:
        K.stroke(d, [K.at(0.0, 0.0), K.at(n * 0.3, -1.0), K.at(n * 0.6, 0.8), K.at(n - 6.0, 0.0)], WHITE, 2.6)
        K.stroke(d, [K.at(n - 7.0, 0.0), K.at(n - 1.0, -3.6), K.at(n + 3.0, -2.6)], WHITE, 2.2)
        K.stroke(d, [K.at(n - 7.0, 0.0), K.at(n - 1.0, 3.6), K.at(n + 2.0, 3.6)], WHITE, 2.2)
        K.oval(d, K.at(n + 0.6, 0.2), 2.8, 2.8, WHITE)
        K.oval(d, K.at(n * 0.45, 2.6), 2.2, 1.2, WHITE)

    def detail(d) -> None:
        K.oval(d, K.at(n + 0.6, 0.2), 2.8, 2.8, STONE)
        K.oval(d, K.at(n, -0.6), 1.0, 1.0, WHITE)
        K.oval(d, K.at(n * 0.45, 2.6), 2.2, 1.2, LEAF)
        K.line(d, [K.at(4.0, 0.6), K.at(n * 0.3, -0.4), K.at(n * 0.6, 1.4)], WOOD_DARK, 0.5)

    return K.solid(("staff", length), shape, WOOD, detail, outline=1.0, rim=0.3, shade=0.35, shade_colour=WOOD_DARK)


#: The rows in which her staff is in her near hand, and how it turns from the
#: line of her forearm.
STAFF_ROWS = {"pulsar_beacon": 0.0, "cosmic_garden": -120.0, "taunt": -100.0, "block": -95.0}


def _cloak(ctx) -> List[Stamp]:
    """Her cloak, from her shoulders to her calves, its hem cut like leaves;
    and, when it is not in her hand, her staff across her back."""
    sway = int(round(float(ctx.pose["hem"][0]) * 1.6))
    out: List[Stamp] = []
    # The cloak stops at the floor, and it is short on a trunk that is not
    # upright; the staff is on her back only when she stands.
    upright = abs((ctx.lean + 180.0) % 360.0 - 180.0) < 50.0
    room = ctx.ground - ctx.hip[1]
    hem = int(max(4.0, min(32.0, room - 4.0))) if upright else 6
    if ctx.anim not in STAFF_ROWS and upright and room > 30.0:
        out.append((_staff(), ctx.trunk(-13.0, 14.0), "staff_back", ctx.lean - 62.0))

    def shape(d) -> None:
        pts = [K.at(-4.0, TOP + 1.0), K.at(-10.0, TOP + 6.0), K.at(-11.6, -10.0), K.at(-14.6 - sway, hem - 6.0)]
        for k in range(5):
            x = -14.6 - sway + (18.6 + sway) * (k + 0.5) / 5.0
            pts += [K.at(x - 1.0, float(hem)), K.at(x + 0.8, hem - 5.0)]
        pts += [K.at(4.0, hem - 6.0), K.at(3.0, TOP + 2.0)]
        K.poly(d, pts, WHITE)

    def detail(d) -> None:
        K.poly(d, [K.at(-6.0, TOP + 12.0), K.at(4.0, TOP + 12.0), K.at(4.0, 34.0), K.at(-8.0 - sway * 0.5, 34.0)], NIGHT)
        for x, y in ((-3.0, -18.0), (0.6, -6.0), (-4.6, 4.0), (-1.0, 16.0), (-5.6, 24.0)):
            K.oval(d, K.at(x, y), 0.8, 0.8, GOLD)
        K.line(d, [K.at(-8.0, TOP + 8.0), K.at(-11.6 - sway * 0.6, 24.0)], CLOAK_DARK, 0.7)

    out.append((K.solid(("druid_cloak", sway, hem), shape, CLOAK, detail, outline=1.3, rim=0.2, shade=0.4, shade_colour=CLOAK_DARK), ctx.hip, "cloak", ctx.lean))
    return out


X.layers["back"].append(_cloak)
X.layers["back"].append(_mane)


def _hair_shape(d) -> None:
    K.oval(d, K.at(-1.0, -4.4), 9.4, 8.8, WHITE)
    K.poly(d, [K.at(-9.4, -4.0), K.at(-10.6, 4.0), K.at(-8.6, 9.6), K.at(-3.6, 9.0), K.at(-1.6, 1.0)], WHITE)


def _hair(d) -> None:
    # Parted at the side; it comes down past her ear and her jaw.
    K.poly(d, [K.at(20.0, -8.6), K.at(8.6, -8.6), K.at(5.6, -7.0), K.at(2.4, -4.4), K.at(0.0, -2.6), K.at(-1.4, 1.0), K.at(-2.0, 5.0), K.at(-2.6, 10.0),
               K.at(-20.0, 10.0), K.at(-20.0, -26.0), K.at(20.0, -26.0)], HAIR)
    # The silver in it.
    for strand in ([(6.0, -9.6), (1.0, -8.0), (-2.6, -3.0), (-4.0, 4.0)], [(2.0, -11.0), (-4.0, -8.0), (-7.6, -1.0), (-8.0, 6.0)]):
        K.line(d, [K.at(x, y) for x, y in strand], HAIR_LIGHT, 0.8)


def _face(d) -> None:
    # The lines of a face that has smiled a great deal.
    crease = mix(SKIN, SKIN_DEEP, 0.4)
    K.line(d, [K.at(0.4, 2.6), K.at(-0.6, 4.0)], crease, 0.45)
    K.line(d, [K.at(4.6, 4.4), K.at(3.2, 6.0)], crease, 0.45)
    K.oval(d, K.at(-1.0, 5.6), 0.9, 1.1, GOLD)


_head = R.make_head(K, ("anne",), SKIN, SKIN_SHADE, SKIN_DEEP, skull=(0.0, -2.2, 7.8, 8.6), jaw=(2.2, 3.6, 5.6, 6.8),
                    nose=((7.2, 0.6), (9.0, 3.0), (8.6, 4.0), (7.2, 4.2)), ear=None, shape=_hair_shape, under=_hair, over=_face)
_eyes = R.make_eyes(K, (2.4, -0.2), (7.4, -0.4), ink=INK, white=None, lid=INK, size=0.95)
_brows = R.make_brows(K, [(0.2, -3.8), (2.4, -4.6), (4.8, -4.2)], [(6.0, -4.3), (7.4, -4.6), (8.6, -4.2)], HAIR, 0.9)
_mouth = R.make_mouth(K, (5.6, 7.0), (128, 54, 62, 255), wide=0.9, lips=(196, 96, 100, 255))

def _circlet():
    """A band of leaves round her head, and two small antlers."""

    def shape(d) -> None:
        K.poly(d, [K.at(-9.0, -6.6), K.at(9.4, -8.6), K.at(9.4, -6.0), K.at(-9.0, -4.0)], WHITE)
        for x0, lean_ in ((-4.6, -1.0), (3.4, 1.0)):
            K.stroke(d, [K.at(x0, -7.0), K.at(x0 + 1.0 * lean_, -12.6), K.at(x0 + 3.0 * lean_, -17.0)], WHITE, 1.9)
            K.stroke(d, [K.at(x0 + 1.0 * lean_, -12.6), K.at(x0 - 2.4 * lean_, -15.6)], WHITE, 1.6)
            K.stroke(d, [K.at(x0 + 2.0 * lean_, -14.8), K.at(x0 + 5.6 * lean_, -14.6)], WHITE, 1.5)
        for x in (-7.0, -1.0, 6.0):
            K.oval(d, K.at(x, -7.6 - 0.1 * x), 2.6, 1.6, WHITE)

    def detail(d) -> None:
        K.poly(d, [K.at(-20.0, -8.0), K.at(20.0, -12.0), K.at(20.0, 0.0), K.at(-20.0, 0.0)], LEAF_DARK)
        for x in (-7.0, -1.0, 6.0):
            K.oval(d, K.at(x, -7.6 - 0.1 * x), 2.6, 1.6, LEAF)
        K.oval(d, K.at(2.6, -7.4), 1.2, 1.2, GOLD)

    return K.solid(("circlet",), shape, ANTLER, detail, outline=1.1, rim=0.3, shade=0.35, shade_colour=ANTLER_DARK)


X.head_layers = lambda pose: [(_head(), "head"), (_eyes(str(pose["eyes"])), "eyes"), (_brows(R.brow_mood(pose)), "brows"),
                              (_mouth(str(pose["mouth"])), "mouth"), (_circlet(), "circlet")]
X.neck = R.make_neck(K, SKIN_SHADE, 3.8)
# Wide sleeves.
X.upper_arm = lambda near: [(0.0, 1.0, 6.0, 5.8, COAT if near else COAT_DARK)]
X.forearm = lambda near: [(0.0, 0.45, 5.8, 5.6, COAT if near else COAT_DARK), (0.4, 1.0, 4.4, 3.8, SKIN if near else SKIN_SHADE),
                          (0.52, 0.64, 4.8, 4.6, LEAF_DARK), (0.76, 0.88, 4.4, 4.2, LEAF_DARK)]
X.thigh = lambda near: [(0.0, 1.0, 6.8, 5.6, COAT if near else COAT_DARK)]
X.shin = lambda near: [(0.0, 0.5, 5.6, 5.2, COAT if near else COAT_DARK), (0.45, 1.0, 5.8, 5.0, BOOT if near else BOOT_DARK)]
X.hand = R.make_hand(K, SKIN, SKIN_SHADE, SKIN_DEEP, size=0.88)
X.shoe = R.make_shoe(K, BOOT, BOOT_DARK, BUILD.ankle_up, long=0.95)

# ---- How she holds herself ---------------------------------------------------

X.set_rest(na=(5.0, 14.0), fa=(-1.0, 21.5), nh="flat", nf=(-3.6, 0.0, 0.0), ff=(4.6, 0.0, 0.0))


@X.row
def idle(i: int, n: int):
    # A hand at her belt; she listens, and looks up at the sky through the leaves.
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.3 + 0.3 * s), head=(0.2, -0.2 * s, -3.0 + 3.0 * c), eyes="closed" if i == n - 2 else "up" if c < -0.3 else "open")


@X.row
def walk(i: int, n: int):
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 7.6, 4.2)
    return P(hip=(0.5, 0.8 * math.cos(2.0 * ph)), lean=2.0, head=(0.0, 0.0, 1.2 * s), na=(-2.0 - 6.0 * c, 24.0), nh="soft", fa=(2.0 + 6.0 * c, 23.5), nf=nf, ff=ff,
             hem=(1.0 + 1.5 * abs(c), 0.5 + 1.5 * abs(c)))


@X.row
def talk(i: int, n: int):
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.3 * s), head=(0.3, 0.0, 2.5 * s), na=(14.0 + 3.0 * c, 5.0 - 5.0 * max(0.0, s)), nh="open", mouth=("open", "smile", "big", "smile")[i % 4],
             brows=1.0 if s > 0.3 else 0.0)


@X.row
def golden_record_guard(i: int, n: int):
    # She holds the record up in front of her in both hands.
    _, s, _c = loop(i, n)
    return P(hip=(-1.0, 3.0 + 0.3 * s), lean=-4.0, head=(-0.5, 0.0, 4.0), na=(17.0, -2.0), fa=(15.0, 6.0), nh="fist", fh="fist", nf=(-6.0, 0.0, 0.0), ff=(6.0, 0.0, 0.0),
             brows=-1.0, mouth="flat")


@X.row
def whale_song(i: int, n: int):
    # Her hands at her mouth, and she calls; something large answers.
    call = P(lean=-4.0, head=(0.0, 0.0, -8.0), na=(10.0, -5.0), fa=(11.0, -3.0), nh="flat", fh="flat", mouth="o", eyes="closed")
    return X.keys(shot(i, n), [(0.0, P()), (0.2, call), (0.8, dict(call, mouth="open")), (1.0, P(eyes="happy"))])


@X.row
def pulsar_beacon(i: int, n: int):
    # One arm straight up, and the map opens from her hand.
    up = P(hip=(0.0, -0.5), lean=-4.0, head=(0.0, 0.0, -12.0), na=(8.0, -18.0), nab=-1.0, arm="under", nh="fist", eyes="up", mouth="open", brows=1.0)
    return X.keys(shot(i, n), [(0.0, P()), (0.25, up), (0.85, up), (1.0, P())])


@X.row
def cosmic_garden(i: int, n: int):
    # She kneels and puts a hand to the ground, and it comes up green and gold.
    kneel = P(hip=(-1.0, 16.0), lean=22.0, head=(1.0, 0.0, 6.0), na=(13.0, 4.0), nh="fist", fa=(16.0, 20.0), fh="flat", nf=(-11.0, 0.0, 34.0), ff=(9.0, 0.0, 0.0),
              hem=(3.0, 1.0))
    return X.keys(shot(i, n), [(0.0, P()), (0.25, kneel), (0.8, dict(kneel, eyes="happy")), (1.0, kneel)])


@X.row
def voyager_cast(i: int, n: int):
    # She sends it: a long underarm throw, and she watches it go.
    back = P(hip=(-3.0, 3.0), lean=-8.0, na=(-16.0, 12.0), nh="fist", fa=(12.0, 8.0), fh="open", brows=-1.0)
    out = P(hip=(4.0, 3.0), lean=12.0, na=(24.0, -8.0), nh="open", fa=(-8.0, 16.0), nf=(-8.0, 0.0, 10.0), ff=(9.0, 0.0, 0.0), mouth="open", brows=1.0, hem=(4.0, 1.0))
    return X.keys(shot(i, n), [(0.0, P()), (0.3, back), (0.5, out), (0.85, dict(out, eyes="up")), (1.0, P())])


@X.row
def crouch(i: int, n: int):
    # A coat to her calf: she goes down on one knee, she does not squat.
    _, s, _c = loop(i, n)
    return P(hip=(-1.0, 12.0 + 0.4 * s), lean=18.0, head=(1.0, 0.0, -8.0), na=(8.0, 14.0), fa=(4.0, 13.0), nf=(-9.0, 0.0, 24.0), ff=(8.0, 0.0, 0.0), hem=(2.0, 2.0),
             eyes="closed" if i == n - 2 else "open")


@X.row
def crouch_walk(i: int, n: int):
    ph, _s, c = loop(i, n)
    nf, ff = R.stride(ph, 5.6, 2.6)
    return P(hip=(-0.5, 11.0 + 0.6 * math.cos(2.0 * ph)), lean=18.0, head=(1.0, 0.0, -8.0), na=(8.0 - 2.0 * c, 14.0), fa=(4.0 + 2.0 * c, 13.0), nf=nf, ff=ff, hem=(2.0, 2.0))


@X.row
def taunt(i: int, n: int):
    # She sets the foot of her staff on the ground, twice, and the stone lights.
    up = P(na=(13.0, 2.0), nh="fist", lean=-2.0, brows=1.0)
    down = dict(up, na=(13.0, 5.0), hip=(0.0, 1.0))
    return X.keys(shot(i, n), [(0.0, up), (0.25, down), (0.45, up), (0.65, down), (1.0, dict(down, eyes="happy"))])


@X.row
def block(i: int, n: int):
    # Her staff upright in front of her, both hands on it.
    _, s, _c = loop(i, n)
    return P(hip=(-2.0, 4.0 + 0.4 * s), lean=-5.0, na=(13.0, 2.0), fa=(13.0, 9.0), nh="fist", fh="fist", nf=(-7.0, 0.0, 0.0), ff=(7.0, 0.0, 0.0), brows=-1.0, mouth="flat")


X.rows = [("idle", 8, 148), ("walk", 8, 104), ("run", 8, 80), ("crouch", 6, 96), ("crouch_walk", 8, 92), ("jump", 6, 90), ("fall", 6, 92), ("land_hard", 7, 84),
          ("dash_startup", 4, 54), ("dash", 6, 60), ("slide", 6, 68), ("roll", 8, 62), ("wall_grab", 6, 104), ("wall_jump", 6, 82), ("ledge_grab", 6, 98),
          ("ledge_climb", 6, 94), ("climb", 8, 98), ("swim", 8, 104), ("block", 6, 82), ("hit", 5, 84), ("death", 8, 108), ("talk", 8, 106), ("interact", 8, 94),
          ("golden_record_guard", 8, 68), ("whale_song", 10, 74), ("pulsar_beacon", 10, 76), ("cosmic_garden", 10, 78), ("voyager_cast", 10, 66),
          ("celebrate", 8, 90), ("taunt", 8, 96)]

# ---- From the front ------------------------------------------------------------

FRONT_HEM = BUILD.hip_up - 5.0


def _front_robe(d) -> None:
    """Her robe from the front: its neck, the light on her bust and the shade
    under it, her belt and its disc, the folds, and the hem cut like leaves."""
    by = TOP + 12.5
    K.poly(d, [K.at(-3.4, TOP - 1.0), K.at(3.4, TOP - 1.0), K.at(0.0, TOP + 7.0)], SKIN_SHADE)
    K.line(d, [K.at(-3.4, TOP - 1.0), K.at(0.0, TOP + 7.0), K.at(3.4, TOP - 1.0)], COAT_LIGHT, 1.0)
    for sx in (-1.0, 1.0):
        K.oval(d, K.at(4.4 * sx, by + 0.2), 2.6, 2.0, mix(COAT, COAT_LIGHT, 0.45))
        K.poly(d, [K.at(0.8 * sx, by + 4.4), K.at(4.4 * sx, by + 5.2), K.at(8.4 * sx, by + 3.4), K.at(7.6 * sx, by + 6.0), K.at(4.2 * sx, by + 7.0), K.at(0.8 * sx, by + 6.0)],
               COAT_DARK)
    K.poly(d, [K.at(-9.0, -14.4), K.at(9.0, -14.4), K.at(9.0, -11.2), K.at(-9.0, -11.2)], SCARF)
    K.oval(d, K.at(0.0, -12.8), 2.6, 2.6, GOLD, OUTLINE, 0.5)
    K.oval(d, K.at(0.0, -12.8), 1.4, 1.4, None, GOLD_DARK, 0.5)  # type: ignore[arg-type]
    K.poly(d, [K.at(-1.0, -10.4), K.at(1.0, -10.4), K.at(0.8, 2.0), K.at(-0.8, 2.0)], SCARF)
    for x in (-6.0, -2.6, 2.6, 6.0):
        K.line(d, [K.at(x * 0.8, -9.0), K.at(x * 1.5, FRONT_HEM - 6.0)], COAT_DARK, 0.6)
    for k in range(-5, 6):
        x = k * 3.4
        K.poly(d, [K.at(x - 1.7, FRONT_HEM - 7.0), K.at(x + 1.7, FRONT_HEM - 7.0), K.at(x, FRONT_HEM - 0.6)], COAT_LIGHT)


def _front_hair_shape(d) -> None:
    # Long, down each side of her face to her shoulders; and her antlers.
    K.oval(d, K.at(0.0, -5.4), 10.0, 8.0, WHITE)
    for sx in (-1.0, 1.0):
        K.poly(d, [K.at(7.0 * sx, -6.0), K.at(10.6 * sx, 0.0), K.at(11.0 * sx, 12.0), K.at(8.6 * sx, 17.0), K.at(5.6 * sx, 13.0), K.at(6.4 * sx, 4.0)], WHITE)
        K.stroke(d, [K.at(3.4 * sx, -8.0), K.at(4.6 * sx, -13.6), K.at(7.0 * sx, -18.0)], WHITE, 1.9)
        K.stroke(d, [K.at(4.6 * sx, -13.6), K.at(1.6 * sx, -16.6)], WHITE, 1.6)
        K.stroke(d, [K.at(5.8 * sx, -15.8), K.at(9.4 * sx, -15.4)], WHITE, 1.5)


def _front_hair(d) -> None:
    K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, 20.0), K.at(6.2, 20.0), K.at(6.4, 4.0), K.at(7.2, -2.0), K.at(5.0, -6.4), K.at(0.0, -8.8), K.at(-5.0, -6.4),
               K.at(-7.2, -2.0), K.at(-6.4, 4.0), K.at(-6.2, 20.0), K.at(-20.0, 20.0)], HAIR)
    K.line(d, [K.at(0.0, -13.0), K.at(0.0, -8.8)], (30, 26, 34, 255), 0.5)
    for sx in (-1.0, 1.0):
        K.line(d, [K.at(7.6 * sx, -4.0), K.at(9.0 * sx, 4.0), K.at(8.4 * sx, 13.0)], HAIR_LIGHT, 0.7)
        K.line(d, [K.at(2.0 * sx, -12.0), K.at(6.0 * sx, -9.0)], HAIR_LIGHT, 0.5)


def _front_circlet(d) -> None:
    # The circlet of leaves and her antlers, her nose, and an earring each side.
    for sx in (-1.0, 1.0):
        for seg in ([(3.4, -8.0), (4.6, -13.6), (7.0, -18.0)], [(4.6, -13.6), (1.6, -16.6)], [(5.8, -15.8), (9.4, -15.4)]):
            K.line(d, [K.at(x * sx, y) for x, y in seg], ANTLER, 1.1)
        K.oval(d, K.at(7.8 * sx, 5.0), 0.9, 0.9, GOLD)
    K.poly(d, [K.at(-8.6, -8.4), K.at(8.6, -8.4), K.at(8.6, -5.8), K.at(-8.6, -5.8)], LEAF_DARK)
    for x in (-6.4, -3.2, 0.0, 3.2, 6.4):
        K.oval(d, K.at(x, -7.4), 1.9, 1.4, LEAF)
    K.oval(d, K.at(0.0, -7.2), 1.1, 1.1, GOLD)
    K.line(d, [K.at(-0.4, -0.4), K.at(-1.2, 3.4), K.at(0.0, 4.2), K.at(1.2, 3.4)], SKIN_DEEP, 0.6)


X.front_torso = R.make_front_torso(K, ("anne",), COAT, COAT_DARK, [(TOP, 3.6), (TOP + 3.6, 7.6), (TOP + 12.5, 9.0), (-13.0, 6.4), (0.0, 8.6), (FRONT_HEM, 12.4)],
                                   shoulder=(6.0, -30.2, 3.8, 4.2), detail=_front_robe)
X.front_head_layers = R.front_face(
    R.make_front_head(K, ("anne",), SKIN, SKIN_DEEP, wide=7.8, jaw=6.4, chin=3.8, shape=_front_hair_shape, hair=_front_hair, face=_front_circlet),
    R.make_front_eyes(K, ("anne",), white=None, ink=INK, spread=3.2, y=-0.4, lash=0.5), R.make_front_brows(K, ("anne",), HAIR, spread=3.2, y=-3.6, width=0.9),
    R.make_front_mouth(K, ("anne",), y=8.2, colour=(128, 54, 62, 255), lips=(196, 96, 100, 255), wide=0.8))
X.front_shoe = R.make_front_shoe(K, BOOT, BOOT_DARK, BUILD.ankle_up, wide=0.9)
X.front_span = (7.2, 4.4)
R.add_front_rows(X)

# ---- What she shows ----------------------------------------------------------


def _record(radius: float, turn: int = 0):
    """The golden record."""
    r = radius

    def shape(d) -> None:
        K.oval(d, K.home, r, r, WHITE)

    def detail(d) -> None:
        for k in (0.82, 0.62, 0.42):
            K.oval(d, K.home, r * k, r * k, None, GOLD_DARK, 0.5)  # type: ignore[arg-type]
        K.oval(d, K.home, r * 0.2, r * 0.2, GOLD_PALE)
        a = math.radians(turn)
        K.line(d, [K.home, K.at(r * 0.8 * math.cos(a), r * 0.8 * math.sin(a))], GOLD_PALE, 0.6)

    return K.solid(("record", radius, turn), shape, GOLD, detail, outline=1.1, rim=0.4, shade=0.4, shade_colour=GOLD_DARK)


def _pulsar_map(lines: int):
    """The map of the pulsars: lines out from one point, each with its marks."""
    angles = (200, 172, 150, 124, 96, 70, 40, 14, -18, -46, -80, -112, -140, 228)
    lengths = (20, 14, 24, 12, 18, 26, 13, 22, 16, 24, 12, 20, 15, 18)

    def paint(d) -> None:
        for k in range(lines):
            a = math.radians(angles[k])
            end = K.at(lengths[k] * math.cos(a), lengths[k] * math.sin(a))
            K.line(d, [K.home, end], GOLD_DARK, 2.0)
            K.line(d, [K.home, end], GOLD, 0.8)
            for t in (0.5, 0.75):
                q = (lerp(K.home[0], end[0], t), lerp(K.home[1], end[1], t))
                K.oval(d, q, 0.8, 0.8, GOLD_PALE)
        K.oval(d, K.home, 2.4, 2.4, GOLD_DARK)
        K.oval(d, K.home, 1.5, 1.5, GOLD_PALE)

    return K.aligned(("pulsar_map", lines), paint)


def _whale(size: float):
    k = size

    def shape(d) -> None:
        K.oval(d, K.home, 11.0 * k, 4.6 * k, WHITE)
        K.poly(d, [K.at(8.0 * k, -1.0 * k), K.at(15.0 * k, -5.0 * k), K.at(13.0 * k, 0.0), K.at(15.0 * k, 4.0 * k), K.at(8.0 * k, 1.0 * k)], WHITE)
        K.poly(d, [K.at(-2.0 * k, 3.0 * k), K.at(1.0 * k, 8.0 * k), K.at(3.0 * k, 3.6 * k)], WHITE)

    def detail(d) -> None:
        K.oval(d, K.at(-2.0 * k, 3.0 * k), 9.0 * k, 2.6 * k, mix(SONG, WHITE, 0.6))
        K.oval(d, K.at(-7.0 * k, -0.8 * k), 0.8, 0.8, INK)

    return K.solid(("whale", size), shape, SONG, detail, outline=1.0, rim=0.3, shade=0.4, shade_colour=SONG_DARK)


def _waves(count: int):
    def shape(d) -> None:
        for j in range(count):
            r = 5.0 + 4.0 * j
            K.stroke(d, [K.at(r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) for a in range(-46, 47, 8)], WHITE, 1.4)

    return R.chalk(K, ("song", count), shape, SONG, SONG_DARK)


def _sprout(tall: int, star: bool):
    def paint(d) -> None:
        stem = [K.at(1.6 * math.sin(y / 4.0), -float(y)) for y in range(0, tall + 1, 2)]
        K.stroke(d, stem, LEAF_DARK, 2.6)
        K.stroke(d, stem, LEAF, 1.2)
        for y, sx in ((tall * 0.4, -1.0), (tall * 0.7, 1.0)):
            K.oval(d, K.at(sx * 2.6 + 1.6 * math.sin(y / 4.0), -y), 2.4, 1.3, LEAF, LEAF_DARK, 0.5)
        if star:
            K.star4(d, K.at(1.6 * math.sin(tall / 4.0), -tall - 3.0), 3.2, GOLD)

    return K.aligned(("sprout", tall, star), paint)


def _spark(size: float):
    def paint(d) -> None:
        K.star4(d, K.home, size, GOLD)
        K.star4(d, K.home, size * 0.45, WHITE, None, 0.0, 0.4)

    return K.piece(("anne_spark", size), paint)


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    anim, i, u = ctx.anim, ctx.i, ctx.u
    stone = None
    if anim in STAFF_ROWS:
        turn = math.degrees(math.atan2(ctx.hand[1] - ctx.elbow[1], ctx.hand[0] - ctx.elbow[0])) + STAFF_ROWS[anim]
        if anim in ("cosmic_garden", "taunt", "block"):
            turn = -88.0  # It stands on the ground.
        a = math.radians(turn)
        foot = (ctx.hand[0] - 30.0 * math.cos(a), ctx.hand[1] - 30.0 * math.sin(a))
        if turn == -88.0:
            foot = (ctx.hand[0] + 1.0, ctx.ground - 1.0)
            reach = max(40, 2 * int((ctx.ground - ctx.hand[1] + 26.0) // 2))
        else:
            reach = 62
        out.append((_staff(reach), foot, "staff", turn))
        stone = (foot[0] + (reach + 0.6) * math.cos(a), foot[1] + (reach + 0.6) * math.sin(a))
    if anim == "golden_record_guard":
        mid = ((ctx.hand[0] + ctx.far_hand[0]) / 2.0 + 6.0, (ctx.hand[1] + ctx.far_hand[1]) / 2.0)
        out.append((_record(12.0, 45 * i), mid, "record", 0.0))
    elif anim == "whale_song" and 0.2 <= u <= 0.9:
        out.append((_waves(1 + i % 3), (ctx.head[0] + 16.0, ctx.head[1] + 4.0), "song", 0.0))
        if u >= 0.45:
            out.append((_whale(1.0), (ctx.head[0] + 46.0, ctx.head[1] - 12.0 + 2.0 * math.sin(ctx.phase)), "whale", -8.0))
    elif anim == "pulsar_beacon" and 0.25 <= u <= 0.9:
        out.append((_pulsar_map(min(14, 2 + 2 * int((u - 0.25) / 0.08))), pin(stone), "map", 0.0))  # type: ignore[arg-type]
    elif anim == "cosmic_garden" and u >= 0.25:
        grow = min(1.0, (u - 0.25) / 0.5)
        for k, (dx, tall) in enumerate(((10.0, 14), (20.0, 20), (30.0, 12))):
            h = 2 * int(round(tall * grow / 2.0))
            if h >= 4:
                out.append((_sprout(h, grow > 0.8), pin((ctx.far_hand[0] + dx - 4.0, ctx.ground - 1.0)), f"sprout_{k}", 0.0))
    elif anim == "voyager_cast":
        if u < 0.45:
            out.append((_record(7.0, 60 * i), (ctx.hand[0] + 3.0, ctx.hand[1] + 1.0), "record", 0.0))
        else:
            t = (u - 0.45) / 0.55
            out.append((_record(7.0, 60 * i), (ctx.hand[0] + 10.0 + 40.0 * t, ctx.hand[1] - 8.0 - 26.0 * t), "record", 0.0))
            out.append((_spark(3.0), (ctx.hand[0] + 4.0 + 30.0 * t, ctx.hand[1] - 2.0 - 18.0 * t), "spark", 0.0))
    elif anim == "celebrate":
        out.append((_spark(4.0), (ctx.head[0] - 24.0, ctx.head[1] - 22.0), "spark_0", 0.0))
        out.append((_spark(3.0), (ctx.head[0] + 28.0, ctx.head[1] - 20.0), "spark_1", 0.0))
    elif anim == "taunt" and u >= 0.2 and stone is not None:
        out.append((_spark(3.0 + (i % 2)), stone, "spark", 0.0))
    elif anim == "interact" and 0.35 <= u <= 0.7:
        out.append((_spark(3.0), (ctx.hand[0] + 16.0, ctx.hand[1] - 5.0), "spark", 0.0))
    return out


X.effects = _effects

# Her dialogue portraits: the painted ones of the sheet before this.
PORTRAIT_SIZE = (192, 192)


def render_portraits(out_dir, **opts):
    """Her portraits are frames of this sheet."""
    del opts
    return X.portraits(out_dir, {
        "default": ("idle", (0,), 0, False),
        "speaking": ("talk", tuple(range(8)), 108, True),
        "wonder": ("idle", tuple(range(8)), 118, True),
        "listening": ("idle", (6,), 0, False),
        "whale_song": ("whale_song", tuple(range(1, 9)), 112, True),
        "pale_blue_dot": ("idle", (3,), 0, False),
    }, view_width=46.0, size=PORTRAIT_SIZE)
render_frame = X.render_frame

ROWS = X.rows
_render_frame = X.render_frame
render, main, render_canonical = R.entry_points(X, ACTOR_METADATA, DISPLAY_NAME)


# ---- In the round (``_person_round``, ``_round_wear``) ------------------------
#
# Her pieces placed in 3D. Her own art draws her where she has it: her head
# and robe in her three-quarter view (and its mirror; her hair is parted at
# the side, so the left one shows the part on the other side) and in her front
# view, her cloak, hair and staff in her three-quarter view; her sleeves,
# hands, boots and neck in every view. What 3D draws is data: a head, a robe,
# a cloak, the circlet and the antlers. Her rows do not use this.

import numpy as np  # noqa: E402

from . import _person_round as O  # noqa: E402
from . import _round_wear as W  # noqa: E402

J = O.person_joints(X, stagger=2.0)
#: Her near hand flat at her belt, her far hand at her side.
HANDS = {"r": (J.wrist(True, -4.4), (-1.0, 0.3, -0.6)), "l": (J.wrist(False, 8.6), (1.0, 0.0, -0.2))}

HEAD_3D = O.Head3D(
    skin=SKIN, shade=SKIN_SHADE, deep=SKIN_DEEP,
    skull=((0.0, -2.2, 0.0), (7.8, 8.6, 7.8)), jaw=((0.0, 3.6, 3.1), (6.4, 6.8, 3.6)), nose=((0.0, 2.0, 8.0), (1.0, 2.2, 2.2)), ear=None,
    eye=(24.0, -0.3), eye_size=0.95, ink=INK, lid=INK, brow=(HAIR, None, -4.2, 0.9),
    # Her hair: all of her head but her face, long down her back and to her
    # shoulders each side of her face.
    hair=lambda u, v: (v < -8.2 + 1.4 * (u / 60.0) ** 2) | (np.abs(u) > 56.0),
    hair_colour=HAIR, hair_shade=mix(HAIR, INK, 0.4), volumes=[((0.0, 3.0, -2.6), (9.0, 12.0, 8.4)), ((0.0, -6.4, -0.8), (8.6, 5.6, 8.4))],
    lines=[O.curve([(-2.4, 7.4, 6.0), (0.0, 7.9, 6.3), (2.4, 7.4, 6.0)], (196, 96, 100, 255), 1.2),
           O.curve([(-2.4, 7.4, 6.1), (0.0, 7.7, 6.4), (2.4, 7.4, 6.1)], (128, 54, 62, 255), 0.6),
           O.curve([(0.0, -12.6, 2.4), (0.0, -9.0, 5.4)], (30, 26, 34, 255), 0.5)]
    + [O.curve([O.on_ellipsoid((0.0, 3.0, -2.6), (9.0, 12.0, 8.4), u + 6.0 * t, -2.0 + 12.0 * t, 0.2)[0] for t in (0.0, 0.5, 1.0)], HAIR_LIGHT, 0.7)
       for u in (-150.0, -110.0, -80.0, 80.0, 110.0, 150.0)],
)

#: Her robe: to her ankles, open at the neck, light on her bust and in shade
#: under it, belted with the record for its buckle, folds down the skirt, and
#: its hem cut like leaves.
ROBE = W.Trunk(
    rings=[O.Ring(TOP, 0.0, 0.6, 3.6, 3.2), O.Ring(-33.4, 0.0, 0.6, 7.6, 6.1), O.Ring(-24.5, 0.0, 1.4, 9.0, 8.0), O.Ring(-13.0, 0.0, 0.2, 6.4, 6.0),
           O.Ring(0.0, 0.0, 0.0, 8.6, 7.6), O.Ring(20.0, 0.0, 0.0, 10.4, 9.0), O.Ring(FRONT_HEM, 0.0, 0.0, 12.4, 10.3)],
    garment=W.Garment(COAT, COAT_DARK, radius=8.6, features=[
        W.Neckline(TOP - 1.0, TOP + 7.0, 24.0, SKIN_SHADE),
        W.Glow(28.0, TOP + 12.7, 2.6, 2.0, mix(COAT, COAT_LIGHT, 0.45), both=True),
        W.Across(-70.0, 70.0, TOP + 18.2, COAT_DARK, width=1.2),
        W.Band(-14.4, -11.2, SCARF), W.Dot(0.0, -12.8, 2.6, GOLD, ring=GOLD_DARK), W.Strip(0.0, -10.4, 2.0, 1.0, SCARF),
        W.Down(20.0, -9.0, FRONT_HEM - 7.0, COAT_DARK, spread=8.0), W.Down(-20.0, -9.0, FRONT_HEM - 7.0, COAT_DARK, spread=8.0),
        W.Down(55.0, -9.0, FRONT_HEM - 7.0, COAT_DARK, spread=10.0), W.Down(-55.0, -9.0, FRONT_HEM - 7.0, COAT_DARK, spread=10.0),
        W.PointedHem(FRONT_HEM - 7.0, FRONT_HEM - 0.6, 3.4, COAT_LIGHT, under=COAT_DARK), W.Shade()]),
    shoulder=((-6.0, -30.2, 0.4), (3.8, 4.2, 3.8)),
)
#: Her cloak, from her shoulders to her calves, round her back only, its hem
#: cut like leaves.
CLOAK_3D = W.Cloak(
    rings=[O.Ring(-36.0, 0.0, -0.6, 6.8, 5.8), O.Ring(-31.0, 0.0, -1.0, 10.4, 8.4), O.Ring(-12.0, 0.0, -1.4, 10.8, 8.6), O.Ring(10.0, 0.0, -1.8, 11.6, 9.4),
           O.Ring(30.0, 0.0, -2.2, 12.6, 10.2)],
    garment=W.Garment(CLOAK, CLOAK_DARK, radius=10.0, features=[W.PointedHem(24.0, 30.0, 4.0, CLOAK_DARK), W.Down(160.0, -28.0, 24.0, CLOAK_DARK)]),
    turns=(115.0, 245.0),
)
#: The circlet of leaves round her head, a gold leaf in front; her antlers.
CIRCLET = W.Hat(crown=[O.Ring(-8.6, 0.0, 0.0, 8.5, 8.5), O.Ring(-6.2, 0.0, 0.0, 8.7, 8.7)], brim=None, under=LEAF_DARK,
                garment=W.Garment(LEAF_DARK, LEAF_DARK, radius=8.6, features=[W.Glow(float(u), -7.4, 1.9, 1.3, LEAF) for u in range(-165, 180, 30)]
                                  + [W.Dot(0.0, -7.3, 1.1, GOLD)]))
#: Each antler is her front view's (across and up); its beam sweeps back and
#: its tines go forward, so it branches from the side as well.
ANTLERS = [[(s * 3.4, -8.0, 2.0), (s * 4.6, -13.6, 0.8), (s * 7.0, -18.0, -1.6)] for s in (-1.0, 1.0)] + \
          [[(s * 4.6, -13.6, 0.8), (s * 1.6, -16.6, 3.6)] for s in (-1.0, 1.0)] + [[(s * 5.8, -15.8, -0.2), (s * 9.4, -15.4, 1.6)] for s in (-1.0, 1.0)]
_BACK_SHOE = R.make_back_shoe(K, BOOT, BOOT_DARK, BUILD.ankle_up, wide=0.9)


def round_figure() -> O.Figure:
    """Anne Druid in the round, as she rests."""
    head = np.asarray(J.head)
    own_trunk = O.own_art("own_robe", (0.0, 0.0, 0.0), lambda: X.torso(0, 0), X.front_torso, lead=0.4)
    own_head = O.own_art("own_head", J.head, lambda: O.composed(K, X.head_layers(J.rest)), lambda: O.composed(K, X.front_head_layers(dict(R.FRONT_REST))),
                         lead=9.0)
    own_back = O.own_layers(X, ["back"])
    not_head, not_back = O.not_in(own_head.when), O.not_in(own_back.when)
    trunk, head3d, cloak, circlet = ROBE.part(), O.head_part(HEAD_3D, J.head), CLOAK_3D.part(), CIRCLET.part(J.head)
    trunk.when, head3d.when, circlet.when, cloak.when = O.not_in(own_trunk.when), not_head, not_head, not_back
    hair = W.mane(K, [tuple(head + d) for d in ((0.0, -1.0, -7.4), (0.0, 5.0, -9.2), (0.0, 11.0, -10.2), (0.0, 17.0, -10.8), (0.0, 23.0, -11.2),
                                               (0.0, 28.0, -11.4))], 5.4, HAIR, HAIR_LIGHT, back_width=12.0, lead=1.0)
    hair.when = not_back
    parts = [trunk, head3d, cloak, circlet, own_trunk, own_head, own_back, hair,
             W.prop(K, "staff", (-7.4, 14.0, -12.0), (11.0, -44.0, -10.0), _staff, when=not_back),
             W.strokes(K, "antlers", [[tuple(head + p) for p in ln] for ln in ANTLERS], 1.8, ANTLER, ANTLER_DARK, tuple(head + (0.0, -12.0, 2.0)), lead=2.0,
                       when=not_head),
             O.person_neck(X, J.neck, J.throat)]
    for side, hand in zip(("r", "l"), ("nh", "fh")):
        target, pole = HANDS[side]
        elbow, wrist = O.two_bone(J.shoulders[side], target, BUILD.upper, BUILD.fore, pole)
        knee, ankle = O.two_bone(J.hips[side], J.ankles[side], BUILD.thigh, BUILD.shin, (0.0, 0.0, 1.0))
        parts += [O.person_arm(X, f"{side}_arm", J.shoulders[side], elbow, wrist, str(J.rest[hand])), O.person_leg(X, f"{side}_leg", J.hips[side], knee, ankle),
                  O.shoes(f"{side}_boot", ankle, X.shoe, X.front_shoe, _BACK_SHOE)]
    return O.Figure(parts, X.frame, X.cx, X.ground, BUILD.hip_up, trunk=(0.0, -20.0, 0.4))


def render_turnaround(path):
    """Her eight views, with her own art (three quarters and the front) under
    the views it draws."""
    rows = {name: n for name, n, _ms in X.rows}
    own = {"front_3q": X.render_frame("idle", 0, rows["idle"]), "front": X.render_frame("front", 0, rows["front"])}
    return O.turnaround(K, round_figure(), path, title=f"{DISPLAY_NAME} in the round", own=own)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


if __name__ == "__main__":
    raise SystemExit(main())
