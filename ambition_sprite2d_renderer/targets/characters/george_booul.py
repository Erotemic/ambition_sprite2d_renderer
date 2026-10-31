"""Classic sheet-ghost sprite target for George Boo'l.

George Boo'l is a playful George Boole parody.  He is deliberately rendered as
an unmistakable old-fashioned bedsheet ghost: one draped cloth silhouette, two
eye holes, a mouth hole, sheet corners lifted by the fists under them, and a
scalloped hem.  He is posed as cloth: the dome leads, the bell bends after it
and the hem trails, and a corner reaching out pulls the sheet with it.  Every
view turns (render_view, render_turnaround); the game's rows face +x
at three quarters.  Boolean ideas appear in the animation language rather than
through a busy costume:

* TRUE is the ordinary pale sheet state;
* FALSE is the inverted charcoal sheet state;
* NOT flips between those states;
* AND focuses two inputs into one green logic discharge;
* a failed proposition makes the sheet collapse like abandoned laundry.

The mixed cast of humans, animals, machines, ghosts, and other beings is normal
in Ambition.  Nobody needs to explain why Boo'l is a ghost.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageChops, ImageDraw, ImageFilter
from ambition_sprite2d_renderer.core.draw import blending_draw

from ...authoring import rigdoc
from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.sheet_build import build_sheet

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "george_booul"
FRAME_SIZE = (160, 160)
SUPER = 4
W, H = FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER
CENTER_X = 80.0
GROUND_Y = 137.0

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 132),
    ("idle_false", 8, 132),
    ("drift", 8, 96),
    ("toggle_state", 8, 88),
    ("and_zap", 8, 78),
    ("not_fade", 8, 92),
    ("hit", 5, 88),
    ("death", 8, 112),
    ("taunt", 8, 104),
    # The fight rows. Each is slaved to its move (frame = floor(progress x
    # frames)), so `ATTACK_WINDOWS` keys the strike pose to the move's live
    # windows; the ms here only matter to a preview.
    ("jab", 10, 25),
    # His second and third jab are borrowed (`smash_duelist_a`'s jab2 and
    # jab3) and name `attack`: one row keyed to both.
    ("attack", 12, 40),
    ("attack_side", 10, 53),
    ("attack_up", 10, 51),
    ("attack_down", 10, 53),
    ("dash_attack", 10, 50),
    ("smash_forward", 12, 78),
    ("smash_up", 12, 73),
    ("smash_down", 12, 74),
    ("air_neutral", 10, 36),
    ("air_forward", 10, 55),
    ("air_back", 10, 58),
    ("air_up", 10, 35),
    ("air_down", 10, 63),
    ("special", 14, 51),
    ("special_side", 12, 62),
    ("special_up", 12, 96),
    ("special_down", 12, 72),
    ("special_air_down", 12, 50),
]

SHEET_FILES = [
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
]

AUTHORING_DESCRIPTION = (
    "George Boo'l parodies George Boole, whose algebra of true/false values "
    "became foundational to logic and computing. The design intentionally uses "
    "the simplest possible Halloween bedsheet ghost silhouette. Boolean ideas "
    "are expressed through state inversion and attack staging rather than a "
    "literal scholar costume: white sheet means TRUE, charcoal sheet means "
    "FALSE, NOT flips the palette, AND merges two inputs, and defeat leaves an "
    "empty sheet on the floor. The name is pronounced like 'George Boole' with "
    "a ghostly 'boo' emphasized."
)

GAMEPLAY_DESCRIPTION = (
    "Suggested gameplay role: lightweight hovering trap-zoner. Boo'l drifts "
    "smoothly, changes between TRUE and FALSE states, and converts placed logic "
    "marks into short ranged bursts. TRUE should favor readable setup and "
    "control; FALSE can favor feints, brief fades, and counterplay. His attacks "
    "should feel clean and binary rather than visually noisy."
)

SUGGESTED_BARKS = {
    "idle": [
        "True. False. Boo.",
        "A tidy proposition, at last.",
        "Mind the operator.",
    ],
    "provoked": [
        "Then let us test your premise.",
        "That does not follow.",
    ],
    "on_hit": [
        "An invalid operation!",
        "You wrinkled the proof!",
    ],
    "victory": [
        "The proposition stands.",
        "Decided conclusively.",
    ],
}

FALLBACK_DIALOGUE = [
    "A proposition does not become true merely because it is loud.",
    "Elegant systems survive contact with inconvenient examples.",
    "Most confusion is only a missing operator wearing a dramatic hat.",
    "I haunt the space between yes and no. It is busier than one expects.",
]

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_george_booul",
        "actor_id": "george_booul",
        "display_name": "George Boo'l",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "locomotion_hint": "Hover",
        "traits": [
            "story",
            "ghost",
            "logic",
            "boolean",
            "playable_candidate",
        ],
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": True,
            "climb": None,
            "fly": True,
            "swim": None,
            "crawl": None,
            "use_lifts": True,
            "door_access": ["public", "service"],
        },
        "interactions": {
            "talk": True,
            "trade": None,
            "carry": None,
            "open_doors": ["public", "service"],
        },
    },
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "peaceful"},
    "visual": {"default_pose": "idle", "music_cue": "scholar_haunt"},
    "dialogue_hints": {
        "barks": [line for lines in SUGGESTED_BARKS.values() for line in lines],
        "fallback_dialogue": FALLBACK_DIALOGUE,
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "drift", "events": []},
        "interaction.talk": {"animation": "taunt", "events": []},
        "action.cast.primary": {"animation": "and_zap", "events": []},
        "action.cast.secondary": {"animation": "toggle_state", "events": []},
        "action.special": {"animation": "not_fade", "events": []},
        "damage.hit": {"animation": "hit", "events": []},
        "lifecycle.death": {"animation": "death", "events": []},
    },
    "sockets": {
        "head": {"source": "george_booul.geometry", "point": {"x": 80.0, "y": 48.0}},
        "chest": {"source": "george_booul.geometry", "point": {"x": 80.0, "y": 82.0}},
        "hand_l": {"source": "george_booul.geometry", "point": {"x": 57.0, "y": 81.0}},
        "hand_r": {"source": "george_booul.geometry", "point": {"x": 111.0, "y": 81.0}},
        "speech_bubble": {"source": "george_booul.geometry", "point": {"x": 80.0, "y": 13.0}},
        "focus": {"source": "george_booul.geometry", "point": {"x": 80.0, "y": 63.0}},
    },
    "tags": ["story", "ghost", "logic", "boolean", "playable_candidate"],
}

INK = (20, 25, 30, 255)
TRUE_CLOTH = (238, 243, 232, 255)
TRUE_LIGHT = (255, 255, 249, 255)
TRUE_SHADOW = (186, 201, 196, 255)
TRUE_LINE = (64, 77, 88, 255)
FALSE_CLOTH = (52, 50, 61, 255)
FALSE_LIGHT = (94, 88, 108, 255)
FALSE_SHADOW = (29, 29, 37, 255)
FALSE_LINE = (10, 10, 14, 255)
TRUE_EYE = (19, 28, 27, 255)
FALSE_EYE = (244, 106, 53, 255)
LOGIC_GREEN = (113, 231, 135, 255)
LOGIC_GREEN_LIGHT = (205, 255, 192, 255)
LOGIC_RED = (244, 95, 60, 255)
LOGIC_GOLD = (244, 211, 104, 255)

#: The camera's turn about him: 0 faces the viewer, 90 faces +x. The sheet
#: shows his heading by where the face sits on the dome and which corner is
#: in front; the game's rows face +x at three quarters.
GAME_YAW = 40.0
#: The dome, the bell of the sheet, and its hem at rest.
HEAD_R = 22.0
HEAD_AT = (CENTER_X, 52.0)
HEM_Y = 129.0
HEM_HALF = 33.0
LINE_W = 1.5
FIST_R = 5.5
HAND_MARGIN = 18.0


@dataclass
class Pose:
    """One frame of the sheet. The head leads and the cloth follows: ``lean``
    carries the dome over (+ toward his heading) and ``hem_dx`` drags the hem,
    so the bell bends between them. A hand is a fist under a sheet corner,
    placed by its offset from where it rests (``near_*`` is the corner on
    the viewer's side, ``far_*`` the one behind him)."""

    state: float = 1.0
    x: float = 0.0
    y: float = 0.0
    tilt: float = 0.0
    lean: float = 0.0
    stretch: float = 0.0
    hem_dx: float = 0.0
    hem_spread: float = 1.0
    flutter: float = 1.0
    near_x: float = 0.0
    near_y: float = 0.0
    far_x: float = 0.0
    far_y: float = 0.0
    eyes: str = "round"
    eye_scale: float = 1.0
    mouth_open: float = 0.0
    blink: bool = False
    opacity: float = 1.0
    squash_x: float = 1.0
    squash_y: float = 1.0
    fx: str = ""
    fx_strength: float = 0.0
    collapse: float = 0.0
    phase: float = 0.0
    yaw: float = GAME_YAW


def _s(value: float) -> int:
    return max(1, round(value * SUPER))


def _pt(x: float, y: float) -> Point:
    return (x * SUPER, y * SUPER)


def _box(x0: float, y0: float, x1: float, y1: float) -> Tuple[int, int, int, int]:
    return (
        round(x0 * SUPER),
        round(y0 * SUPER),
        round(x1 * SUPER),
        round(y1 * SUPER),
    )


def _rgba(color: RGBA, alpha: float = 1.0) -> RGBA:
    return (
        color[0],
        color[1],
        color[2],
        max(0, min(255, round(color[3] * alpha))),
    )


def _lerp_color(a: RGBA, b: RGBA, t: float) -> RGBA:
    t = max(0.0, min(1.0, t))
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(4))  # type: ignore[return-value]


def _smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _downsample(img: Image.Image) -> Image.Image:
    return rigdoc.downsampled_canvas(img, FRAME_SIZE, Image.Resampling.LANCZOS)


def _pose(animation: str, frame_idx: int, nframes: int) -> Pose:
    p = Pose()
    phase = frame_idx / max(1, nframes)
    t = frame_idx / max(1, nframes - 1)
    wave = math.sin(phase * math.tau)
    wave2 = math.sin(phase * math.tau * 2.0)
    p.phase = phase

    if animation in ("idle", "idle_false"):
        sign = 1.0 if animation == "idle" else -1.0
        p.state = 1.0 if animation == "idle" else 0.0
        p.y = -2.5 * (0.5 - 0.5 * math.cos(phase * math.tau))
        p.lean = 1.6 * wave * sign
        p.hem_dx = -1.4 * wave * sign
        p.near_y = 2.0 * wave
        p.far_y = -2.0 * wave
        p.near_x = 1.0 * wave2
        p.blink = frame_idx == (6 if animation == "idle" else 2)
        if animation == "idle_false":
            p.eye_scale = 1.0 + 0.08 * wave2
    elif animation == "drift":
        # His walk: the dome leads, the hem streams behind and sways.
        p.x = 1.5 * wave
        p.y = -3.0 * abs(wave)
        p.lean = 6.0 + 1.5 * wave
        p.hem_dx = -7.0 - 2.0 * wave
        p.flutter = 1.7
        p.near_x, p.near_y = -5.0, 3.0 + 2.0 * wave
        p.far_x, p.far_y = -6.0, 3.0 - 2.0 * wave
    elif animation == "toggle_state":
        # NOT, staged: a full turn of the sheet that comes round inverted.
        flip = _smoothstep(t)
        bump = math.sin(t * math.pi)
        p.state = 1.0 - flip
        p.y = -5.0 * bump
        p.tilt = 360.0 * t
        p.squash_x = 1.0 - 0.3 * bump
        p.squash_y = 1.0 + 0.18 * bump
        p.near_x, p.near_y = 14.0 * bump, -18.0 * bump
        p.far_x, p.far_y = -14.0 * bump, -18.0 * bump
        p.eyes = "wide" if 0.2 < t < 0.8 else "round"
        p.fx = "toggle"
        p.fx_strength = bump
    elif animation == "and_zap":
        # AND: one input in each corner, brought together and fired forward.
        charge = math.sin(t * math.pi)
        spread = _smoothstep(min(1.0, t * 2.0))
        meet = _smoothstep((t - 0.4) / 0.4)
        p.y = -3.0 * charge
        p.lean = 4.0 * meet
        p.hem_dx = -4.0 * meet
        p.near_x = 18.0 * spread * (1.0 - meet) + 34.0 * meet
        p.near_y = -16.0 * spread * (1.0 - meet) - 6.0 * meet
        p.far_x = -18.0 * spread * (1.0 - meet) + 52.0 * meet
        p.far_y = -16.0 * spread * (1.0 - meet) - 6.0 * meet
        p.eyes = "narrow"
        p.mouth_open = 0.3 + 0.4 * charge
        p.fx = "and"
        p.fx_strength = charge
    elif animation == "not_fade":
        pulse = math.sin(t * math.pi)
        p.state = 1.0 - _smoothstep(min(1.0, t * 1.2))
        p.y = -6.0 * pulse
        p.x = 4.0 * math.sin(t * math.tau)
        p.lean = -5.0 * pulse
        p.hem_dx = 4.0 * pulse
        p.flutter = 1.5
        p.near_x, p.near_y = 8.0 * pulse, -26.0 * pulse
        p.far_x, p.far_y = -8.0 * pulse, -26.0 * pulse
        p.opacity = 1.0 - 0.55 * pulse
        p.eyes = "wide"
        p.mouth_open = 0.6 * pulse
        p.fx = "not"
        p.fx_strength = pulse
    elif animation == "hit":
        # Struck: the dome snaps back, the hem keeps going, the corners fly up.
        impact = math.sin(t * math.pi)
        p.x = -7.0 * impact
        p.y = 2.0 * impact
        p.lean = -12.0 * impact
        p.hem_dx = 7.0 * impact
        p.tilt = 7.0 * impact
        p.flutter = 1.0 + impact
        p.near_x, p.near_y = -12.0 * impact, -30.0 * impact
        p.far_x, p.far_y = -10.0 * impact, -26.0 * impact
        p.eyes = "wide" if impact > 0.3 else "round"
        p.mouth_open = 0.8 * impact
        p.fx = "hit"
        p.fx_strength = impact
    elif animation == "death":
        # The proof fails: a recoil, then the sheet settles empty on the floor.
        if t < 0.3:
            u = _smoothstep(t / 0.3)
            p.lean = -10.0 * u
            p.hem_dx = 6.0 * u
            p.y = -4.0 * u
            p.near_x, p.near_y = -8.0 * u, -24.0 * u
            p.far_x, p.far_y = -8.0 * u, -22.0 * u
            p.eyes = "wide"
            p.mouth_open = 0.7 * u
        else:
            u = _smoothstep((t - 0.3) / 0.7)
            p.lean = -10.0 * (1.0 - u)
            p.hem_dx = 6.0 * (1.0 - u)
            p.y = -4.0 * (1.0 - u)
            p.near_x, p.near_y = -8.0 + 4.0 * u, -24.0 + 44.0 * u
            p.far_x, p.far_y = -8.0 + 12.0 * u, -22.0 + 42.0 * u
            p.squash_x = 1.0 + 0.5 * u
            p.squash_y = 1.0 - 0.72 * u
            p.hem_spread = 1.0 + 0.25 * u
            p.flutter = 1.0 - 0.8 * u
            p.eyes = "wide" if u < 0.25 else "closed"
            p.mouth_open = 0.7 * (1.0 - u)
            p.opacity = 1.0 - 0.15 * u
            p.collapse = u
    elif animation in ATTACK_POSES:
        return _attack_pose(animation, frame_idx, nframes)
    elif animation == "taunt":
        # BOO: both corners thrown up, the mouth at its widest.
        raise_ = _smoothstep(min(1.0, t * 3.0)) * (1.0 - _smoothstep((t - 0.8) / 0.2))
        p.y = -4.0 * raise_ - 1.5 * (0.5 + 0.5 * wave2)
        p.stretch = -4.0 * raise_
        p.lean = 2.0 * wave
        p.flutter = 1.0 + raise_
        p.near_x, p.near_y = (14.0 + 4.0 * wave2) * raise_, -50.0 * raise_
        p.far_x, p.far_y = (-10.0 - 4.0 * wave2) * raise_, -48.0 * raise_
        p.eyes = "happy" if raise_ > 0.5 else "round"
        p.mouth_open = 0.2 + 0.8 * raise_
    return p


#: Where each fight row's move is live, as parts of the move (start, end),
#: read off his table (`data/characters/george_booul/smash_moveset.ron`:
#: window start / move duration). Keep them in step with the table: the
#: strike pose is drawn on exactly the frames these cover.
ATTACK_WINDOWS = {
    "jab": [(0.2, 0.4)],
    "attack": [(0.12, 0.45)],
    "attack_side": [(0.34, 0.491)],
    "attack_up": [(0.314, 0.49)],
    "attack_down": [(0.321, 0.472)],
    "dash_attack": [(0.3, 0.48)],
    "smash_forward": [(0.426, 0.511)],
    "smash_up": [(0.409, 0.523)],
    "smash_down": [(0.382, 0.506)],
    "air_neutral": [(0.167, 0.5)],
    "air_forward": [(0.327, 0.491)],
    "air_back": [(0.345, 0.483)],
    "air_up": [(0.2, 0.457)],
    "air_down": [(0.349, 0.492)],
    "special": [(0.423, 0.521), (0.592, 0.704)],
    "special_side": [(0.27, 0.432)],
    "special_up": [(0.157, 0.278)],
    "special_down": [(0.395, 0.674)],
    "special_air_down": [(0.267, 0.667)],
}

#: The poses of a fight row, as changes to the rest pose: `wind` is the
#: anticipation before the hit, `strike` (one per live window) the hit itself.
#: He faces +x. Each strike reaches toward its move's hitbox (the table's
#: offsets): the dome leads into it, the hem trails out of it, and the fist
#: under a sheet corner is the striking point. The far reach of a hit is its
#: strike effect's; the sheet sells where it comes from.
ATTACK_POSES = {
    # Hitbox (26, 0): a quick near-corner poke.
    "jab": {
        "wind": dict(lean=-2.0, near_x=-6.0, eyes="narrow"),
        "strike": [dict(x=3.0, lean=5.0, hem_dx=-4.0, near_x=34.0, near_y=-6.0, eyes="narrow", mouth_open=0.3)],
    },
    # Jab 2 and 3: the far corner crosses in front of him.
    "attack": {
        "wind": dict(lean=1.0, near_x=-4.0, far_x=6.0, eyes="narrow"),
        "strike": [dict(x=5.0, lean=7.0, hem_dx=-6.0, far_x=80.0, far_y=-8.0, near_x=-6.0, near_y=6.0,
                        eyes="narrow", mouth_open=0.4, flutter=1.4)],
    },
    # Hitbox (36, -2): a lunge on the near corner, the far one behind it.
    "attack_side": {
        "wind": dict(x=-4.0, lean=-6.0, hem_dx=4.0, near_x=-10.0, near_y=-10.0, eyes="narrow"),
        "strike": [dict(x=7.0, lean=10.0, hem_dx=-10.0, near_x=40.0, near_y=-4.0, far_x=30.0, far_y=-4.0,
                        squash_x=1.05, squash_y=0.96, eyes="narrow", mouth_open=0.5, flutter=1.5)],
    },
    # Hitbox (10, -30): both corners swept up over the dome.
    "attack_up": {
        "wind": dict(y=3.0, squash_x=1.08, squash_y=0.9, near_y=4.0, far_y=4.0),
        "strike": [dict(stretch=-6.0, squash_x=0.92, squash_y=1.1, lean=3.0, near_x=14.0, near_y=-56.0,
                        far_x=-12.0, far_y=-54.0, eyes="narrow", mouth_open=0.6, flutter=-1.0)],
    },
    # Hitbox (30, 14): low, the corners along the floor.
    "attack_down": {
        "wind": dict(y=-2.0, near_y=-14.0, eyes="narrow"),
        "strike": [dict(y=1.0, squash_x=1.1, squash_y=0.86, lean=8.0, hem_dx=-4.0, near_x=38.0, near_y=30.0,
                        far_x=24.0, far_y=28.0, hem_spread=1.1, eyes="narrow", mouth_open=0.4)],
    },
    # Hitbox (24, -2): the whole sheet thrown forward.
    "dash_attack": {
        "wind": dict(lean=4.0, hem_dx=-6.0, near_x=4.0, eyes="narrow"),
        "strike": [dict(x=10.0, lean=14.0, tilt=-8.0, hem_dx=-16.0, flutter=2.0, near_x=38.0, near_y=-2.0,
                        far_x=56.0, far_y=0.0, eyes="narrow", mouth_open=0.6)],
    },
    # Hitboxes (46, -4) and (16, -4): AND, both corners driven forward as one.
    "smash_forward": {
        "wind": dict(x=-8.0, lean=-10.0, hem_dx=6.0, near_x=-22.0, near_y=-12.0, far_x=-14.0, far_y=-12.0,
                     squash_x=0.96, squash_y=1.04, eyes="narrow", mouth_open=0.1),
        "strike": [dict(x=12.0, lean=16.0, tilt=-3.0, hem_dx=-14.0, near_x=40.0, near_y=-4.0, far_x=70.0,
                        far_y=-2.0, squash_x=1.06, squash_y=0.96, eyes="wide", mouth_open=0.9,
                        fx="and", fx_strength=1.0, flutter=2.0)],
    },
    # Hitbox (6, -38): crouched low, then flung tall with both corners up.
    "smash_up": {
        "wind": dict(y=7.0, squash_x=1.16, squash_y=0.82, near_x=-4.0, near_y=10.0, far_x=4.0, far_y=10.0,
                     eyes="narrow"),
        "strike": [dict(y=-2.0, stretch=-3.0, squash_x=0.88, squash_y=1.12, near_x=16.0, near_y=-50.0,
                        far_x=-16.0, far_y=-48.0, eyes="wide", mouth_open=0.85, fx="uplift", fx_strength=1.0,
                        flutter=-1.5)],
    },
    # Hitbox (0, 16), 44 wide: risen with both corners up, then slammed flat.
    "smash_down": {
        "wind": dict(y=-9.0, stretch=-3.0, near_x=10.0, near_y=-52.0, far_x=-10.0, far_y=-50.0, eyes="narrow"),
        "strike": [dict(y=1.0, squash_x=1.35, squash_y=0.74, near_x=18.0, near_y=40.0, far_x=-20.0,
                        far_y=40.0, hem_spread=1.2, eyes="narrow", mouth_open=0.8, fx="slam", fx_strength=1.0,
                        flutter=1.8)],
    },
    # Hitbox (0, 0) about him: a whirl with both corners flung wide.
    "air_neutral": {
        "wind": dict(near_x=-4.0, near_y=-4.0, far_x=4.0, far_y=-4.0, squash_x=0.95, squash_y=1.04),
        "strike": [dict(near_x=22.0, near_y=-4.0, far_x=-22.0, far_y=-4.0, hem_spread=1.15, flutter=1.5,
                        eyes="narrow", mouth_open=0.5, spin=360.0)],
    },
    # Hitbox (34, -2): the near corner raised, then chopped down and forward.
    "air_forward": {
        "wind": dict(lean=-4.0, near_x=-2.0, near_y=-48.0, eyes="narrow"),
        "strike": [dict(x=4.0, lean=10.0, hem_dx=-8.0, near_x=40.0, near_y=8.0, eyes="narrow",
                        mouth_open=0.5, flutter=1.2)],
    },
    # Hitbox (-36, 0): the far corner swung out behind him.
    "air_back": {
        "wind": dict(lean=4.0, far_x=4.0, eyes="narrow"),
        "strike": [dict(x=-5.0, lean=-12.0, hem_dx=8.0, tilt=6.0, far_x=-46.0, far_y=-6.0, near_x=-10.0,
                        near_y=4.0, eyes="narrow", mouth_open=0.5, flutter=-1.2)],
    },
    # Hitbox (2, -32): a quick sweep of both corners overhead.
    "air_up": {
        "wind": dict(y=3.0, squash_x=1.05, squash_y=0.94),
        "strike": [dict(y=-4.0, squash_x=0.93, squash_y=1.08, near_x=14.0, near_y=-48.0, far_x=-12.0,
                        far_y=-46.0, eyes="narrow", mouth_open=0.5)],
    },
    # Hitbox (6, 32): a stomp, the sheet driven down to a point.
    "air_down": {
        "wind": dict(y=-5.0, near_x=-6.0, near_y=-24.0, far_x=6.0, far_y=-24.0),
        "strike": [dict(y=10.0, squash_x=0.88, squash_y=1.18, near_x=12.0, near_y=-46.0, far_x=-12.0,
                        far_y=-44.0, hem_spread=0.85, flutter=1.8, eyes="narrow", mouth_open=0.6,
                        fx="stomp", fx_strength=0.8)],
    },
    # Bivalence, (0, -6) about him: TRUE thrown open, then FALSE.
    "special": {
        "wind": dict(y=4.0, squash_x=1.1, squash_y=0.86, near_x=-6.0, near_y=6.0, far_x=6.0, far_y=6.0,
                     eyes="narrow"),
        "strike": [
            dict(squash_x=1.12, squash_y=1.08, near_x=26.0, near_y=-16.0, far_x=-26.0, far_y=-16.0,
                 hem_spread=1.15, eyes="wide", mouth_open=0.7, fx="toggle", fx_strength=1.0),
            dict(state=0.0, y=-6.0, squash_x=1.2, squash_y=1.12, near_x=30.0, near_y=-30.0, far_x=-30.0,
                 far_y=-30.0, hem_spread=1.2, eyes="wide", mouth_open=0.9, fx="not", fx_strength=1.0),
        ],
    },
    # Modus ponens, (40, 0): the near corner points, and the inference fires.
    "special_side": {
        "wind": dict(x=-4.0, lean=-6.0, near_x=-14.0, near_y=-6.0, far_x=-10.0, far_y=-6.0, eyes="narrow"),
        "strike": [dict(x=5.0, lean=8.0, hem_dx=-8.0, near_x=42.0, near_y=-8.0, far_x=12.0, far_y=-2.0,
                        eyes="narrow", mouth_open=0.6, fx="and", fx_strength=1.0)],
    },
    # The excluded middle, (2, -30): his recovery, a rise with the hem streaming.
    "special_up": {
        "wind": dict(y=6.0, squash_x=1.12, squash_y=0.84, eyes="narrow"),
        "strike": [dict(y=-2.0, stretch=-3.0, squash_x=0.89, squash_y=1.11, near_x=14.0, near_y=-48.0,
                        far_x=-14.0, far_y=-46.0, flutter=2.0, eyes="wide", mouth_open=0.7, fx="uplift",
                        fx_strength=1.0)],
        # A recovery: the rise is held while he goes up.
        "hold": 0.6,
    },
    # Reductio, (4, 30): the slam, in FALSE.
    "special_down": {
        "wind": dict(y=-8.0, stretch=-3.0, near_x=10.0, near_y=-50.0, far_x=-10.0, far_y=-48.0, eyes="narrow"),
        "strike": [dict(state=0.0, y=1.0, squash_x=1.36, squash_y=0.72, near_x=18.0, near_y=38.0, far_x=-20.0,
                        far_y=38.0, hem_spread=1.2, eyes="narrow", mouth_open=0.8, fx="slam", fx_strength=1.0,
                        flutter=1.8)],
    },
    # Reductio in the air, (4, 30): the stomp, in FALSE.
    "special_air_down": {
        "wind": dict(y=-6.0, near_x=-6.0, near_y=-30.0, far_x=6.0, far_y=-30.0, eyes="narrow"),
        "strike": [dict(state=0.0, y=10.0, squash_x=0.86, squash_y=1.2, near_x=12.0, near_y=-48.0, far_x=-12.0,
                        far_y=-46.0, hem_spread=0.85, flutter=2.0, eyes="narrow", mouth_open=0.7, fx="stomp",
                        fx_strength=1.0)],
    },
}

_LERPED = ("state", "x", "y", "tilt", "lean", "stretch", "hem_dx", "hem_spread", "flutter", "near_x", "near_y",
           "far_x", "far_y", "eye_scale", "mouth_open", "squash_x", "squash_y", "fx_strength")


def _blend(a: dict, b: dict, k: float) -> dict:
    """Pose `a` toward `b` by `k` (each an override of the rest pose)."""
    rest = Pose()
    out = {}
    for name in _LERPED:
        va = a.get(name, getattr(rest, name))
        vb = b.get(name, getattr(rest, name))
        out[name] = va + (vb - va) * k
    out["fx"] = b.get("fx", "") if k >= 0.5 else a.get("fx", "")
    out["eyes"] = b.get("eyes", "round") if k >= 0.5 else a.get("eyes", "round")
    return out


def _attack_pose(animation: str, frame_idx: int, nframes: int) -> Pose:
    """A fight row's frame: rest, anticipation, the strike on every frame
    that shows a live window, then the follow-through back to rest."""
    spec = ATTACK_POSES[animation]
    windows = ATTACK_WINDOWS[animation]
    lo, hi = frame_idx / nframes, (frame_idx + 1) / nframes
    mid = (lo + hi) / 2.0
    wind, strikes = spec["wind"], spec["strike"]
    pose: dict
    spin = 0.0
    live = [k for k, (a, b) in enumerate(windows) if lo < b and hi > a]
    if live:
        k = live[-1]
        a, b = windows[k]
        pose = dict(strikes[min(k, len(strikes) - 1)])
        turn = pose.pop("spin", 0.0)
        if turn:
            spin = turn * max(0.0, min(1.0, (mid - a) / max(1e-6, b - a)))
    elif mid < windows[0][0]:
        pose = _blend({}, wind, _smoothstep(mid / windows[0][0]))
    elif mid > windows[-1][1]:
        last = dict(strikes[min(len(windows), len(strikes)) - 1])
        last.pop("spin", None)
        b = windows[-1][1]
        hold = spec.get("hold", 0.0)
        u = (mid - b) / max(1e-6, 1.0 - b)
        u = max(0.0, (u - hold) / max(1e-6, 1.0 - hold))
        pose = _blend(last, {}, _smoothstep(u))
    else:
        # Between two live windows: half way back to the anticipation.
        prev = next(k for k, (a, b) in reversed(list(enumerate(windows))) if b <= mid)
        last = dict(strikes[min(prev, len(strikes) - 1)])
        last.pop("spin", None)
        pose = _blend(last, wind, 0.5)
    p = Pose(**{name: pose.get(name, getattr(Pose(), name)) for name in _LERPED})
    p.fx = pose.get("fx", "")
    p.eyes = pose.get("eyes", "round")
    p.tilt += spin
    p.phase = mid
    return p


def _sheet_palette(state: float):
    cloth = _lerp_color(FALSE_CLOTH, TRUE_CLOTH, state)
    light = _lerp_color(FALSE_LIGHT, TRUE_LIGHT, state)
    shadow = _lerp_color(FALSE_SHADOW, TRUE_SHADOW, state)
    eyes = _lerp_color(FALSE_EYE, TRUE_EYE, state)
    outline = _lerp_color(FALSE_LINE, TRUE_LINE, state)
    return cloth, light, shadow, eyes, outline


def _draw_fx(draw: ImageDraw.ImageDraw, p: Pose, cx: float, cy: float) -> None:
    alpha = p.opacity
    if p.fx == "toggle":
        radius = 22.0 + 20.0 * p.fx_strength
        draw.arc(
            _box(cx - radius, cy - radius, cx + radius, cy + radius),
            start=20,
            end=330,
            fill=_rgba(LOGIC_GOLD, alpha),
            width=_s(2.0),
        )
        draw.line(
            [_pt(cx - radius * 0.75, cy - radius * 0.5), _pt(cx + radius * 0.75, cy + radius * 0.5)],
            fill=_rgba(LOGIC_RED, alpha),
            width=_s(2.2),
        )
    elif p.fx == "and":
        strength = p.fx_strength
        left = (cx - 33.0, cy - 2.0)
        right = (cx + 33.0, cy - 2.0)
        focus = (cx, cy + 4.0)
        for px, py in (left, right):
            draw.ellipse(
                _box(px - 4.0, py - 4.0, px + 4.0, py + 4.0),
                fill=_rgba(LOGIC_GREEN_LIGHT, alpha),
                outline=_rgba(INK, alpha),
                width=_s(0.8),
            )
            draw.line(
                [_pt(px, py), _pt(focus[0], focus[1])],
                fill=_rgba(LOGIC_GREEN, strength * alpha),
                width=_s(2.0 + strength),
            )
        beam_end = cx + 32.0 + 28.0 * strength
        draw.line(
            [_pt(focus[0], focus[1]), _pt(beam_end, focus[1])],
            fill=_rgba(LOGIC_GREEN_LIGHT, strength * alpha),
            width=_s(3.0 + 2.0 * strength),
        )
        draw.line(
            [_pt(focus[0], focus[1]), _pt(beam_end, focus[1])],
            fill=_rgba(LOGIC_GREEN, strength * alpha),
            width=_s(1.2 + strength),
        )
    elif p.fx == "not":
        radius = 18.0 + 15.0 * p.fx_strength
        draw.ellipse(
            _box(cx - radius, cy - radius, cx + radius, cy + radius),
            outline=_rgba(LOGIC_RED, p.fx_strength * alpha),
            width=_s(1.8),
        )
        draw.line(
            [_pt(cx - radius * 0.70, cy - radius * 0.70), _pt(cx + radius * 0.70, cy + radius * 0.70)],
            fill=_rgba(LOGIC_RED, p.fx_strength * alpha),
            width=_s(2.0),
        )
    elif p.fx == "uplift":
        # Rays of gold off the top of the sheet: the rise of a launcher.
        strength = p.fx_strength
        # Off the shoulders, up and out: above the head is outside the frame.
        for side in (-1.0, 1.0):
            for k, lean in enumerate((0.35, 0.75, 1.15)):
                angle = -math.pi / 2 + side * lean
                x0, y0 = cx + side * 26.0, cy - 30.0 + 8.0 * k
                x1 = x0 + math.cos(angle) * (14.0 + 8.0 * strength)
                y1 = y0 + math.sin(angle) * (14.0 + 8.0 * strength)
                draw.line([_pt(x0, y0), _pt(x1, y1)],
                          fill=_rgba(LOGIC_GOLD if k != 1 else LOGIC_GREEN_LIGHT, strength * alpha), width=_s(2.0))
    elif p.fx == "slam":
        # A shock along the floor to both sides of the hem.
        strength = p.fx_strength
        floor = cy + 56.0
        for side in (-1.0, 1.0):
            for ring, reach in ((0, 40.0), (1, 54.0)):
                x = cx + side * (reach + 8.0 * strength)
                draw.arc(_box(x - 9.0, floor - 16.0 + 4.0 * ring, x + 9.0, floor + 2.0),
                         start=180 if side < 0 else 270, end=270 if side < 0 else 360,
                         fill=_rgba(LOGIC_RED if ring else LOGIC_GOLD, strength * alpha), width=_s(2.0))
        draw.line([_pt(cx - 60.0, floor), _pt(cx + 60.0, floor)], fill=_rgba(LOGIC_GOLD, 0.7 * strength * alpha), width=_s(1.4))
    elif p.fx == "stomp":
        # Chevrons under the hem: the sheet drives down.
        strength = p.fx_strength
        base = cy + 54.0
        for k in range(3):
            y = base + 6.0 + 7.0 * k
            w = 16.0 - 4.0 * k
            draw.line([_pt(cx - w, y - 5.0), _pt(cx, y), _pt(cx + w, y - 5.0)],
                      fill=_rgba(LOGIC_RED if k else LOGIC_GOLD, strength * alpha * (1.0 - 0.25 * k)), width=_s(2.0))
    elif p.fx == "hit":
        strength = p.fx_strength
        for angle in (0.0, math.pi * 0.7, math.pi * 1.35):
            x0 = cx + math.cos(angle) * 28.0
            y0 = cy + math.sin(angle) * 24.0
            x1 = cx + math.cos(angle) * (35.0 + 10.0 * strength)
            y1 = cy + math.sin(angle) * (31.0 + 10.0 * strength)
            draw.line(
                [_pt(x0, y0), _pt(x1, y1)],
                fill=_rgba(LOGIC_RED, strength * alpha),
                width=_s(1.5),
            )


# --- The cloth ---------------------------------------------------------------


def _bezier(points: Sequence[Point], t: float) -> Point:
    """De Casteljau: the point at ``t`` of the curve through ``points``' hull."""
    pts = list(points)
    while len(pts) > 1:
        pts = [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t) for a, b in zip(pts, pts[1:])]
    return pts[0]


def _curve(points: Sequence[Point], n: int = 12) -> List[Point]:
    return [_bezier(points, i / n) for i in range(n + 1)]


@dataclass
class _Cloth:
    """The sheet of one pose, in frame pixels before the squash and the turn:
    the spine from the dome to the hem, the bell's half width along it, and
    the hem's scallops."""

    p: Pose
    head: Point
    hem: Point
    half_hem: float

    @classmethod
    def of(cls, p: Pose) -> "_Cloth":
        head = (HEAD_AT[0] + p.x + p.lean, HEAD_AT[1] + p.y + p.stretch)
        hem = (CENTER_X + p.x + p.hem_dx, HEM_Y + p.y)
        return cls(p, head, hem, HEM_HALF * p.hem_spread)

    def spine(self, t: float) -> Point:
        # The cloth hangs straight under the dome and settles straight onto
        # the hem; between them it bends as far as the lean and the trail ask.
        h, m = self.head, self.hem
        span = m[1] - h[1]
        return _bezier([h, (h[0], h[1] + span * 0.4), (m[0], m[1] - span * 0.45), m], t)

    def normal(self, t: float) -> Point:
        a, b = self.spine(max(0.0, t - 0.01)), self.spine(min(1.0, t + 0.01))
        tx, ty = b[0] - a[0], b[1] - a[1]
        n = math.hypot(tx, ty) or 1.0
        return (ty / n, -tx / n)

    def width(self, t: float) -> float:
        neck = HEAD_R * 0.95
        return neck + (self.half_hem - neck) * _smoothstep((t - 0.08) / 0.92) ** 1.15

    def edge(self, t: float, u: float) -> Point:
        """The point ``u`` of the way across the bell at ``t`` (-1 the left
        edge, 1 the right)."""
        s, n, w = self.spine(t), self.normal(t), self.width(t)
        return (s[0] + n[0] * w * u, s[1] + n[1] * w * u)

    def hem_points(self) -> List[Point]:
        """The hem, right corner to left: four scallops whose tips hang and
        flutter, a wave that travels from his front to his back."""
        p = self.p
        right, left = self.edge(1.0, 1.0), self.edge(1.0, -1.0)
        a, b = self.spine(0.97), self.spine(1.0)
        dn = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
        down = ((b[0] - a[0]) / dn, (b[1] - a[1]) / dn)
        pts = []
        steps = 8
        for i in range(steps + 1):
            u = i / steps
            base = (right[0] + (left[0] - right[0]) * u, right[1] + (left[1] - right[1]) * u)
            depth = 7.5 if i % 2 else (3.0 if i in (0, steps) else 0.0)
            depth += p.flutter * 2.4 * math.sin(p.phase * math.tau * 2.0 + u * math.tau * 1.25)
            if i % 2 == 0 and i not in (0, steps):
                depth = min(depth, 2.0)
            pts.append((base[0] + down[0] * depth, base[1] + down[1] * depth))
        return pts

    def outline(self) -> List[Point]:
        n = 18
        right = [self.edge(i / n, 1.0) for i in range(n + 1)]
        left = [self.edge(i / n, -1.0) for i in range(n, -1, -1)]
        return right + self.hem_points() + left

    # The corners. ``side`` 1 is the near corner (the viewer's side; on the
    # right when he faces the viewer), -1 the far one.

    def _turn(self, side: int) -> Tuple[float, float]:
        yaw = math.radians(self.p.yaw)
        return side * math.cos(yaw), side * math.sin(yaw)

    def depth(self, side: int) -> float:
        return self._turn(side)[1]

    def hand(self, side: int) -> Point:
        across, _ = self._turn(side)
        yaw = math.radians(self.p.yaw)
        anchor = self.edge(0.22, across)
        rest = (anchor[0] + across * 14.0 + math.sin(yaw) * 6.0, anchor[1] + 12.0)
        dx, dy = (self.p.near_x, self.p.near_y) if side > 0 else (self.p.far_x, self.p.far_y)
        # A reach stops short of the frame's edge: the strike effect goes on.
        return (max(HAND_MARGIN, min(FRAME_SIZE[0] - HAND_MARGIN, rest[0] + dx)), rest[1] + dy)

    def arm(self, side: int) -> Tuple[List[Point], List[Point], Point]:
        """A sheet corner lifted by the fist under it. The cloth runs from the
        side of the dome over the fist, and hangs from the fist back to the
        bell's side; between two points it sags, as cloth does. Returns the
        corner's outline, the hanging cloth under the arm, and the fist."""
        across, _ = self._turn(side)
        top = self.edge(0.14, across)
        low = self.edge(0.7, across)
        hand = self.hand(side)
        shoulder = self.edge(0.3, across * 0.6)
        dx, dy = hand[0] - shoulder[0], hand[1] - shoulder[1]
        n = math.hypot(dx, dy) or 1.0
        px, py = -dy / n, dx / n
        if py > 0:
            px, py = -px, -py
        over = (hand[0] + px * FIST_R * 0.8, hand[1] + py * FIST_R * 0.8)
        under = (hand[0] - px * FIST_R * 0.8, hand[1] - py * FIST_R * 0.8)

        def sagging(a: Point, b: Point, sag: float) -> List[Point]:
            mid = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0 + sag * abs(b[0] - a[0]))
            return _curve([a, mid, b])

        upper = sagging(top, over, 0.1)
        lower = sagging(under, low, 0.35)
        body = [self.edge(t, across) for t in (0.55, 0.4, 0.25)]
        shape = upper + lower + body
        hanging = lower + [upper[len(upper) // 2]]
        return shape, hanging, hand

    def folds(self) -> List[List[Point]]:
        """The creases from under the dome to the hem's valleys."""
        hem = self.hem_points()
        out = []
        for u, valley in ((-0.55, 6), (-0.05, 4), (0.5, 2)):
            pts = [self.edge(0.3 + 0.62 * k / 8, u * (0.5 + 0.5 * k / 8)) for k in range(9)]
            pts.append(hem[valley])
            out.append(pts)
        return out


def _transform(p: Pose):
    """Squash about the floor under him, then turn about his middle
    (counter-clockwise for a positive ``tilt``, as the sheet always turned)."""
    root = (CENTER_X + p.x, GROUND_Y + p.y)
    pivot = (CENTER_X + p.x, 85.0 + p.y)
    r = math.radians(p.tilt)
    c, s = math.cos(r), math.sin(r)

    def apply(q: Point) -> Point:
        x = root[0] + (q[0] - root[0]) * p.squash_x
        y = root[1] + (q[1] - root[1]) * p.squash_y
        dx, dy = x - pivot[0], y - pivot[1]
        return (pivot[0] + dx * c + dy * s, pivot[1] - dx * s + dy * c)

    return apply


def _mask(size, shapes, circles) -> Image.Image:
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)  # raw-draw-ok: an L mask has no alpha to composite
    for pts in shapes:
        d.polygon([_pt(*q) for q in pts], fill=255)
    for (cx, cy), r in circles:
        d.ellipse(_box(cx - r, cy - r, cx + r, cy + r), fill=255)
    return m


def _shifted(mask: Image.Image, dx: float, dy: float) -> Image.Image:
    out = Image.new("L", mask.size, 0)
    out.paste(mask, (round(dx * SUPER), round(dy * SUPER)))
    return out


def _paint_silhouette(img: Image.Image, shapes, circles, fill: RGBA, line: RGBA) -> Image.Image:
    """One merged piece of cloth: the outline of the union, then its fill.
    Returns the fill's mask."""
    lw = LINE_W
    d = ImageDraw.Draw(img)  # raw-draw-ok: blending_draw here breaks the part replay check (MEASURED 2026-10-30)
    for pts in shapes:
        ring = [_pt(*q) for q in pts]
        d.polygon(ring, fill=line)
        d.line(ring + [ring[0]], fill=line, width=_s(lw * 2.0), joint="curve")
    for (cx, cy), r in circles:
        d.ellipse(_box(cx - r - lw, cy - r - lw, cx + r + lw, cy + r + lw), fill=line)
    m = _mask(img.size, shapes, circles)
    img.paste(Image.new("RGBA", img.size, fill), (0, 0), m)
    return m


def _tone(img: Image.Image, mask: Image.Image, color: RGBA, alpha: float, blur: float = 0.0) -> None:
    if blur:
        mask = mask.filter(ImageFilter.GaussianBlur(blur * SUPER))
    mask = mask.point(lambda v: round(v * alpha))
    img.paste(Image.new("RGBA", img.size, color), (0, 0), mask)


def _clipped(img: Image.Image, clip: Image.Image, paint) -> None:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    paint(blending_draw(layer))
    layer.putalpha(ImageChops.multiply(layer.getchannel("A"), clip))
    img.alpha_composite(layer)


def _paint_face(img: Image.Image, cloth: _Cloth, T, p: Pose, eye_color: RGBA, line: RGBA) -> None:
    """Two eye holes and a mouth on the dome, where his heading puts them,
    and the logic badge on his chest: 1 for TRUE, 0 for FALSE."""
    yaw = math.radians(p.yaw)
    hx, hy = cloth.head
    sx, sy = p.squash_x, p.squash_y
    d = ImageDraw.Draw(img)  # raw-draw-ok: blending_draw here breaks the part replay check (MEASURED 2026-10-30)

    def on_dome(theta: float, drop: float) -> Tuple[Point, float]:
        facing = math.cos(yaw + theta)
        return (hx + HEAD_R * 0.86 * math.sin(yaw + theta), hy + drop), facing

    for theta in (-0.4, 0.4):
        (ex, ey), facing = on_dome(theta, 3.0)
        if facing < 0.18:
            continue
        cx, cy = T((ex, ey))
        ew = 4.9 * p.eye_scale * max(0.35, facing) * sx
        eh = 6.8 * p.eye_scale * sy
        if p.eyes == "wide":
            ew, eh = ew * 1.18, eh * 1.15
        if p.blink or p.eyes == "closed":
            d.line([_pt(cx - ew, cy + 1.0), _pt(cx + ew, cy + 1.0)], fill=eye_color, width=_s(1.8))
            continue
        if p.eyes == "happy":
            d.arc(_box(cx - ew, cy - eh * 0.4, cx + ew, cy + eh * 1.1), start=200, end=340, fill=eye_color,
                  width=_s(2.0))
            continue
        m = Image.new("L", img.size, 0)
        md = ImageDraw.Draw(m)  # raw-draw-ok: an L mask has no alpha to composite
        md.ellipse(_box(cx - ew, cy - eh, cx + ew, cy + eh), fill=255)
        if p.eyes == "narrow":
            # A cut across the top, lower toward his nose: a scowl.
            inner = -1.0 if theta > 0 else 1.0
            md.polygon([_pt(cx - ew * 2, cy - eh * 2), _pt(cx + ew * 2, cy - eh * 2),
                        _pt(cx + ew * 2, cy - eh * (0.55 if inner > 0 else -0.05)),
                        _pt(cx - ew * 2, cy - eh * (-0.05 if inner > 0 else 0.55))], fill=0)
        img.paste(Image.new("RGBA", img.size, eye_color), (0, 0), m)
        if p.state < 0.5 and p.eyes != "narrow":
            d.ellipse(_box(cx - ew * 0.3, cy - eh * 0.4, cx + ew * 0.05, cy - eh * 0.1), fill=LOGIC_GOLD)

    (mx, my), facing = on_dome(0.0, 17.0)
    if facing > 0.1:
        cx, cy = T((mx, my))
        mw = (4.6 + 1.6 * p.mouth_open) * max(0.4, facing) * sx
        mh = (3.0 + 5.5 * p.mouth_open) * sy
        d.ellipse(_box(cx - mw, cy - mh, cx + mw, cy + mh), fill=eye_color)

    # The badge rides the chest, under the face.
    chest = cloth.spine(0.36)
    bx = chest[0] + cloth.width(0.36) * 0.8 * math.sin(yaw)
    facing = math.cos(yaw)
    if facing > 0.05 and p.collapse < 0.5:
        cx, cy = T((bx, chest[1] + 4.0))
        r = 4.2
        true = p.state >= 0.5
        d.ellipse(_box(cx - r * max(0.4, facing), cy - r, cx + r * max(0.4, facing), cy + r),
                  fill=LOGIC_GREEN if true else LOGIC_RED, outline=line, width=_s(0.7))
        if true:
            d.line([_pt(cx, cy - 2.3), _pt(cx, cy + 2.3)], fill=TRUE_LIGHT, width=_s(1.1))
        else:
            d.ellipse(_box(cx - 1.4 * facing, cy - 2.1, cx + 1.4 * facing, cy + 2.1), outline=LOGIC_GOLD,
                      width=_s(0.9))


def _draw_sheet(img: Image.Image, p: Pose) -> None:
    """The ghost, drawn whole for the pose: the far corner behind him, the
    sheet with the near corner as one piece of cloth under one outline, its
    shade and light from the upper right, the folds, then the face."""
    cloth = _Cloth.of(p)
    T = _transform(p)
    cloth_c, light, shadow, eye_color, line = _sheet_palette(p.state)

    def tx(pts):
        return [T(q) for q in pts]

    scale = math.sqrt(p.squash_x * p.squash_y)
    hx, hy = cloth.head
    dome = tx([(hx + HEAD_R * math.cos(a * math.tau / 40), hy + HEAD_R * math.sin(a * math.tau / 40)) for a in range(40)])
    body = tx(cloth.outline())
    order = sorted((1, -1), key=cloth.depth)
    behind = [s for s in order if cloth.depth(s) < -0.05]
    front = [s for s in order if s not in behind]

    if p.fx_strength > 0.01 and p.fx:
        glow = LOGIC_GREEN if p.fx in ("and", "uplift") else LOGIC_RED
        r = 34.0 + 8.0 * p.fx_strength
        cx, cy = T((CENTER_X + p.x, 85.0 + p.y))
        ImageDraw.Draw(img).ellipse(_box(cx - r, cy - r * 1.25, cx + r, cy + r * 1.25),  # raw-draw-ok: blending_draw here breaks the part replay check (MEASURED 2026-10-30)
                                    fill=_rgba(glow, 0.12 * p.fx_strength))

    for side in behind:
        shape, hanging, fist = cloth.arm(side)
        _paint_silhouette(img, [tx(shape)], [(T(fist), FIST_R * scale)], shadow, line)
        _tone(img, _mask(img.size, [tx(hanging)], []), _lerp_color(shadow, line, 0.25), 0.5)

    shapes, circles, hangs = [body, dome], [], []
    for side in front:
        shape, hanging, fist = cloth.arm(side)
        shapes.append(tx(shape))
        circles.append((T(fist), FIST_R * scale))
        hangs.append(tx(hanging))
    m = _paint_silhouette(img, shapes, circles, cloth_c, line)

    # Shade on the lower left, light on the upper right, as the cast is lit.
    _tone(img, ImageChops.subtract(m, _shifted(m, 7.0, -3.0)), shadow, 0.95, blur=0.6)
    for hang in hangs:
        _tone(img, ImageChops.multiply(_mask(img.size, [hang], []), m), shadow, 0.55, blur=0.5)
    _tone(img, ImageChops.subtract(m, _shifted(m, -3.0, 3.0)), light, 0.9, blur=0.4)
    gx, gy = T((hx + HEAD_R * 0.3, hy - HEAD_R * 0.35))
    gleam = _mask(img.size, [], [((gx, gy), HEAD_R * 0.38 * scale)])
    _tone(img, ImageChops.multiply(gleam, m), light, 0.75, blur=2.0)

    def paint_folds(d):
        for fold in cloth.folds():
            d.line([_pt(*T(q)) for q in fold], fill=_rgba(shadow, 0.75), width=_s(1.1), joint="curve")

    _clipped(img, m, paint_folds)
    _paint_face(img, cloth, T, p, eye_color, line)

    if p.fx:
        cx, cy = T((CENTER_X + p.x, 79.0 + p.y))
        _draw_fx(ImageDraw.Draw(img), p, cx, cy)  # raw-draw-ok: blending_draw here breaks the part replay check (MEASURED 2026-10-30)

    if p.opacity < 0.999:
        img.putalpha(img.getchannel("A").point(lambda v: round(v * p.opacity)))


def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    _draw_sheet(img, _pose(animation, frame_idx, nframes))
    return _downsample(img)


#: The turnaround's views, as yaws: front, three quarters, side, three
#: quarters back, back, and the left ones. The sheet is symmetric, so a left
#: view is the right one mirrored.
TURNAROUND_YAWS = (0.0, 45.0, 90.0, 135.0, 180.0, -135.0, -90.0, -45.0)


def render_view(yaw: float, animation: str = "idle", frame_idx: int = 0, nframes: int = 8) -> Image.Image:
    """One frame of ``animation`` seen from ``yaw`` (0 faces the viewer, 90
    faces +x, a negative yaw faces -x)."""
    p = _pose(animation, frame_idx, nframes)
    p.yaw = abs(yaw)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    _draw_sheet(img, p)
    frame = _downsample(img)
    return frame.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if yaw < 0 else frame


def render_turnaround(poses: Sequence[Tuple[str, int, int]] = (("idle", 0, 8), ("taunt", 4, 8))) -> Image.Image:
    """The eight views (columns) of each pose (rows), on one image."""
    fw, fh = FRAME_SIZE
    sheet = Image.new("RGBA", (fw * len(TURNAROUND_YAWS), fh * len(poses)), (0, 0, 0, 0))
    for row, (animation, index, count) in enumerate(poses):
        for col, yaw in enumerate(TURNAROUND_YAWS):
            sheet.alpha_composite(render_view(yaw, animation, index, count), (col * fw, row * fh))
    return sheet


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        label_width=112,
        actor_metadata=ACTOR_METADATA,
        auto_crop=False,
    )
    parts = publish_rig_flipbook(TARGET_NAME, ROWS, render_frame, outputs, frame_transform, Path(out_dir))
    return [
        outputs["canonical"],
        outputs["canonical_transparent"],
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["ron"],
        outputs["actor"],
        outputs["preview"],
    ] + list(parts.values())


__all__ = [
    "ACTOR_METADATA",
    "AUTHORING_DESCRIPTION",
    "FALLBACK_DIALOGUE",
    "FRAME_SIZE",
    "GAMEPLAY_DESCRIPTION",
    "ROWS",
    "SHEET_FILES",
    "SUGGESTED_BARKS",
    "TARGET_NAME",
    "render",
    "render_frame",
    "render_turnaround",
    "render_view",
]
