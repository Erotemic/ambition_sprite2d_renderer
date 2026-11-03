"""Lucy: the oldest guest of the History dimension, in the Cradle.

Lucy is an *Australopithecus afarensis* of 3.2 million years ago (her
skeleton, AL 288-1, was found at Hadar in Ethiopia in 1974; in Ethiopia she
is Dinkinesh). She is not a modern human, so the character generator cannot
draw her; this is her own drawing, from what her bones and her species'
other fossils tell:

- She is small: about 110 cm. She stands and walks upright on two legs (the
  angle of her knee and the shape of her pelvis say so), with a straight leg
  under a wide, flaring hip.
- Her legs are short and her arms are long: her hands hang near her knees.
  Her fingers are long and a little curved, the hands of a climber.
- Her ribcage is a funnel, narrow at the top and wide at the bottom, over a
  round belly. Her shoulders are high.
- Her skull is small (a brain about a third of ours). Her face pushes
  forward in a muzzle, under a low, sloping forehead and a ridge of brow;
  she has no chin. Her nose is flat.
- Her body has hair; her face, hands and feet are bare, dark skin.

She is shy and curious and holds a stone that she found. She talks (in the
game's way); she does not fight.

Rows: ``idle`` (she turns the stone and looks at it, then at you; she
blinks), ``walk`` (upright, short quick steps, arms swinging), ``talk`` (her
mouth moves; she holds the stone up to show it), ``hit`` (she flinches back)
and ``death`` (she sinks down and curls up).

The style is the History cast's (`_history_africa_kit.py`): flat colour with
one shade, a sepia outline. She faces right and stands on ``GROUND``.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Sequence, Tuple

from . import _art_cast_kit as K
from . import _history_africa_kit as A

TARGET_NAME = "history_lucy"
FRAME_SIZE = (128, 160)
GROUND = 152.0
ROWS: List[Tuple[str, int, int]] = [("idle", 8, 160), ("walk", 8, 100), ("talk", 6, 120), ("hit", 3, 90), ("death", 6, 140)]
LOOPS = {"idle", "walk", "talk"}

INK = A.SEPIA_INK
FUR = (118, 76, 46, 255)
FUR_DARK = (82, 52, 32, 255)
FUR_LIGHT = (152, 106, 70, 255)
SKIN = (78, 60, 52, 255)
SKIN_SHADE = (56, 42, 36, 255)
SKIN_LIGHT = (108, 86, 74, 255)
EYE_WHITE = (226, 210, 184, 255)
IRIS = (52, 32, 22, 255)
STONE = (168, 160, 146, 255)
STONE_SHADE = (120, 112, 100, 255)
MOUTH = (46, 24, 20, 255)

#: Her bones, in frame px: the leg (thigh, shin) is short, the arm (upper
#: arm, forearm) long. A hanging hand reaches her knee.
THIGH, SHIN = 21.0, 20.0
UPPER_ARM, FOREARM = 24.0, 23.0

ACTOR_METADATA = {
    "actor": {"character_id": "npc_history_lucy", "display_name": "Lucy"},
    "body": {"body_plan": "Biped", "body_kind": "Standard", "mass_class": "Light",
             "traits": ["australopithecus", "upright", "long_arms", "furred", "holds_a_stone"], "locomotion_hint": "Walk"},
    "visual": {"default_pose": "idle", "portrait": {"animation": "talk", "frame": 1}},
    "tags": ["townsfolk", "history", "cradle", "peaceful"],
    "authoring_description": (
        "A resident of the Cradle in the History dimension: Lucy, an Australopithecus afarensis of 3.2 million years ago, as "
        "her skeleton found at Hadar in Ethiopia in 1974 tells it. Small (110 cm) and upright on short legs, with long arms and "
        "curved fingers, a funnel ribcage over a round belly, a small skull with a forward muzzle, a low forehead, a brow ridge "
        "and no chin; hair on her body, bare dark skin on her face, hands and feet. Shy and curious, holding a stone she found. "
        "Her own drawing (the character generator draws only modern people)."
    ),
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "dialogue.talk": {"animation": "talk", "events": []},
        "combat.hurt": {"animation": "hit", "events": []},
        "combat.death": {"animation": "death", "events": []},
    },
}

Point = Tuple[float, float]


def _plate(f: K.Frame, pts: Sequence[Point], fill, edge: float = 1.0, body: bool = True) -> None:
    """A shape with its own sepia edge."""
    f.poly(K.grow(pts, edge), INK, body=body)
    f.poly(pts, fill, body=False)


def _rod(f: K.Frame, pts: Sequence[Point], width: float, fill, edge: float = 1.0, body: bool = True) -> None:
    """A limb with its own sepia edge."""
    f.limb(pts, width + 2.0 * edge, INK, body=body)
    f.limb(pts, width, fill, body=False)


def _bend(a: Point, b: Point, first: float, second: float, toward: float) -> Point:
    """The middle joint (knee, elbow) of two bones from `a` to `b`; it bends
    toward `toward` (+1: the right of the frame, her front)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = max(1e-3, math.hypot(dx, dy))
    dc = min(d, first + second - 1e-3)
    along = (first * first - second * second + dc * dc) / (2.0 * dc)
    h = math.sqrt(max(0.0, first * first - along * along))
    ux, uy = dx / d, dy / d
    nx, ny = -uy, ux
    if nx * toward < 0:
        nx, ny = -nx, -ny
    return (a[0] + ux * along + nx * h, a[1] + uy * along + ny * h)


def _reach(a: Point, b: Point, length: float) -> Point:
    """`b`, brought within `length` of `a` along the line between them."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy)
    if d <= length:
        return b
    return (a[0] + dx / d * length, a[1] + dy / d * length)


def _tufts(f: K.Frame, base: Sequence[Point], fill, size: float = 2.6) -> None:
    """Little points of hair along a line, pointing away from its left side
    (the outside of a contour drawn clockwise). They are body: the outline
    goes round them."""
    for (x0, y0), (x1, y1) in zip(base, base[1:]):
        dx, dy = x1 - x0, y1 - y0
        d = math.hypot(dx, dy) or 1.0
        nx, ny = dy / d, -dx / d
        mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        f.poly([(x0, y0), (mx + nx * size + dx / d * 0.8, my + ny * size + dy / d * 0.8), (x1, y1)], fill)


def _leg(f: K.Frame, hip: Point, ankle: Point, colour, shade) -> None:
    knee = _bend(hip, ankle, THIGH, SHIN, 1.0)
    _rod(f, [hip, knee], 10.0, colour)
    _rod(f, [knee, (ankle[0], ankle[1] - 1.0)], 7.4, colour)
    f.ink([(hip[0] - 2.0, hip[1] + 3.0), (knee[0] - 2.5, knee[1] - 1.0)], 0.8, shade)
    # The foot: bare skin, an arch, the big toe in line with the others.
    ax, ay = ankle
    foot = [(ax - 4.0, ay - 3.0), (ax + 3.0, ay - 2.4), (ax + 10.0, ay + 1.6), (ax + 12.6, ay + 3.6), (ax + 12.0, ay + 6.0),
            (ax - 4.6, ay + 6.0), (ax - 5.6, ay + 2.0)]
    _plate(f, foot, SKIN)
    f.ink([(ax + 6.0, ay + 3.4), (ax + 9.0, ay + 5.0)], 0.6, SKIN_SHADE)
    f.ink([(ax + 9.4, ay + 3.0), (ax + 11.4, ay + 5.0)], 0.6, SKIN_SHADE)
    # Hair stops at the ankle.
    _tufts(f, [(ax - 4.4, ay - 4.0), (ax - 1.0, ay - 2.4), (ax + 2.6, ay - 3.4)], colour, 1.8)


def _hand(f: K.Frame, wrist: Point, angle: float, grip: float, stone: bool) -> None:
    """A hand at `wrist`, its fingers along `angle` (degrees; 90 is down);
    `grip` 0..1 curls them. With `stone`, it holds the stone."""
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    palm_c = (wrist[0] + ux * 3.6, wrist[1] + uy * 3.6)
    if stone:
        sx, sy = palm_c[0] + ux * 3.0 + nx * 1.5, palm_c[1] + uy * 3.0 + ny * 1.5
        _plate(f, K.ellipse_points(sx, sy, 4.6, 3.8, 18), STONE, edge=0.9)
        f.poly(K.ellipse_points(sx - 1.2, sy + 1.0, 2.8, 1.8, 12), STONE_SHADE, body=False)
        f.dot(sx + 1.4, sy - 1.4, 0.8, K.shade(STONE, 1.35))
    _plate(f, K.ellipse_points(palm_c[0], palm_c[1], 3.6, 3.0, 14), SKIN, edge=0.8)
    # Long, curved fingers: they bend round toward the palm side.
    for k in range(3):
        off = (k - 1) * 1.7
        base = (palm_c[0] + ux * 2.6 + nx * off, palm_c[1] + uy * 2.6 + ny * off)
        mid = (base[0] + ux * 3.4, base[1] + uy * 3.4)
        curl = 1.0 + 2.4 * grip
        tip = (mid[0] + ux * (3.0 - grip) - nx * curl, mid[1] + uy * (3.0 - grip) - ny * curl)
        _rod(f, [base, mid, tip], 1.7, SKIN, edge=0.6)
    thumb = [(palm_c[0] - nx * 2.6, palm_c[1] - ny * 2.6), (palm_c[0] + ux * 2.0 - nx * 4.4, palm_c[1] + uy * 2.0 - ny * 4.4)]
    _rod(f, thumb, 1.8, SKIN, edge=0.6)


def _arm(f: K.Frame, shoulder: Point, hand_at: Point, colour, shade, *, angle: float, grip: float, stone: bool) -> None:
    hand_at = _reach(shoulder, hand_at, UPPER_ARM + FOREARM - 0.5)
    elbow = _bend(shoulder, hand_at, UPPER_ARM, FOREARM, -1.0)
    _rod(f, [shoulder, elbow], 8.0, colour)
    _rod(f, [elbow, hand_at], 6.6, colour)
    f.ink([(shoulder[0] - 1.0, shoulder[1] + 4.0), (elbow[0] - 1.6, elbow[1] - 1.0)], 0.7, shade)
    _tufts(f, [(elbow[0] - 3.0, elbow[1] - 3.0), (elbow[0] - 3.6, elbow[1] + 0.6), (elbow[0] - 1.6, elbow[1] + 3.4)], colour, 2.2)
    _hand(f, hand_at, angle, grip, stone)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    cx = 56.0
    bob = lean = nod = stride = sink = 0.0
    mouth, blink, show, look_up, curl = 0.0, False, 0.0, 0.0, 0.0
    if anim == "idle":
        # She turns the stone over, looks down at it, then up at you.
        look_up = 0.5 + 0.5 * math.sin(cyc)
        nod = 12.0 * (1.0 - look_up) - 2.0
        show = 0.4 + 0.25 * math.sin(cyc * 2.0)
        bob = 0.6 * math.sin(cyc * 2.0)
        blink = i == 5
    elif anim == "walk":
        stride = math.sin(cyc)
        bob = -1.6 * abs(math.cos(cyc))
        lean = 3.0
        nod = 1.0
    elif anim == "talk":
        mouth = 0.5 + 0.5 * math.sin(cyc * 2.0)
        show = 0.7 + 0.3 * math.sin(cyc)
        nod = -3.0 + 3.0 * math.sin(cyc * 2.0)
        look_up = 1.0
    elif anim == "hit":
        lean = -10.0 + 4.0 * t
        nod = -6.0
        mouth = 0.8
        blink = True
        show = 0.1
    elif anim == "death":
        u = min(1.0, t * 1.25)
        sink = 26.0 * u
        lean = 26.0 * u
        nod = 18.0 * u
        curl = u
        blink = t > 0.5
        show = 0.0

    # Her leg is nearly straight when she stands: the hip joint is 39 of the
    # leg's 41 px over the ankle.
    hip = (cx, GROUND - 6.0 - 39.0 - 2.5 + bob + sink)

    def U(dx: float, dy: float) -> Point:
        return K.turn([(hip[0] + dx, hip[1] + dy)], hip[0], hip[1], lean)[0]

    def Us(points) -> List[Point]:
        return [U(x, y) for x, y in points]

    # -- the far arm (behind the body): it hangs, long, and swings -----------
    sh_far = U(4.0, -40.0)
    swing = -9.0 * stride
    far_hand = (sh_far[0] + 4.0 - swing - 8.0 * curl, sh_far[1] + 45.0 - 14.0 * curl)
    _arm(f, sh_far, far_hand, FUR_DARK, K.shade(FUR_DARK, 0.75), angle=95.0 - 2.0 * swing, grip=0.3 + 0.5 * curl, stone=False)

    # -- the far leg ------------------------------------------------------------
    def ankle_of(phase_sign: float, dx: float) -> Point:
        step = stride * phase_sign
        x = hip[0] + dx + 10.0 * step
        lift = 4.5 * max(0.0, math.cos(cyc)) if (anim == "walk" and step > 0) else 0.0
        if anim == "death":
            x = cx + dx + 8.0 * curl
        return (x, GROUND - 6.0 - lift)

    _leg(f, U(-2.0, 2.0), ankle_of(1.0, 1.0), FUR_DARK, K.shade(FUR_DARK, 0.75))

    # -- the body: a funnel ribcage over a round belly, a wide flaring hip ---
    torso = [(-12.0, 4.0), (-13.5, -6.0), (-11.0, -16.0), (-12.5, -28.0), (-10.0, -38.0), (-5.0, -45.0), (2.0, -47.0), (8.0, -44.0),
             (10.5, -35.0), (12.5, -27.0), (17.0, -15.0), (16.5, -4.0), (10.0, 4.0), (0.0, 7.0)]
    _plate(f, Us(torso), FUR)
    # The belly and chest, a lighter coat in front.
    f.poly(Us([(6.0, -36.0), (10.5, -35.0), (12.5, -27.0), (17.0, -15.0), (16.5, -4.0), (10.0, 4.0), (6.0, 2.0), (9.0, -14.0)]), FUR_LIGHT, body=False)
    f.ink(Us([(9.0, -26.0), (11.6, -18.0)]), 0.7, FUR_DARK)
    # The back: hair along it.
    _tufts(f, Us([(-12.5, -28.0), (-13.0, -20.0), (-11.0, -16.0), (-13.5, -6.0), (-12.0, 4.0)])[::-1], FUR, 2.4)
    _tufts(f, Us([(-5.0, -45.0), (-10.0, -38.0), (-12.5, -28.0)]), FUR, 2.6)
    # The flare of the hip bone under the coat.
    f.ink(Us([(-8.0, -9.0), (-2.0, -12.0), (5.0, -10.0)]), 0.8, FUR_DARK)

    # -- the head: small skull, low brow, forward muzzle, no chin -------------
    neck_top = U(7.0, -50.0)
    _rod(f, [U(3.0, -43.0), neck_top], 8.0, FUR)
    hc = U(6.0, -58.0)
    hrot = lean * 0.4 + nod

    def H(dx: float, dy: float) -> Point:
        return K.turn([(hc[0] + dx, hc[1] + dy)], hc[0], hc[1], hrot)[0]

    def Hs(points) -> List[Point]:
        return [H(x, y) for x, y in points]

    jaw = 2.4 * mouth
    skull = [(7.0, -8.0), (1.0, -12.0), (-6.0, -11.0), (-10.5, -6.0), (-11.5, 1.0), (-8.5, 7.0), (-2.0, 9.5), (4.0, 11.5 + jaw),
             (12.0, 13.0 + jaw), (18.0, 11.0 + jaw), (21.0, 8.0 + jaw * 0.6), (22.0, 4.6), (20.6, 0.6), (16.6, -1.6), (16.0, -5.4),
             (14.0, -7.4)]
    _plate(f, Hs(skull), FUR)
    # The bare face: from the low brow to the muzzle and the chinless jaw.
    face = [(5.0, -6.6), (14.0, -7.4), (16.0, -5.4), (16.6, -1.6), (20.6, 0.6), (22.0, 4.6), (21.0, 8.0 + jaw * 0.6),
            (18.0, 11.0 + jaw), (12.0, 13.0 + jaw), (5.0, 11.0 + jaw * 0.5), (2.6, 4.0), (3.0, -2.6)]
    f.poly(Hs(face), SKIN, body=False)
    # The jaw and the cheek in shade; the muzzle catches the light.
    f.poly(Hs([(5.0, 11.0 + jaw * 0.5), (12.0, 13.0 + jaw), (18.0, 11.0 + jaw), (14.0, 9.6 + jaw), (6.0, 7.0)]), SKIN_SHADE, body=False)
    f.poly(Hs([(17.0, 0.4), (20.6, 0.6), (21.6, 4.4), (18.0, 4.2)]), SKIN_LIGHT, body=False)
    # The ridge of the brow, heavy, over a deep-set eye.
    f.poly(Hs([(5.0, -6.6), (14.0, -7.4), (16.0, -5.4), (16.2, -3.6), (12.0, -4.6), (7.0, -4.2)]), SKIN_SHADE, body=False)
    f.ink(Hs([(5.4, -7.2), (14.0, -7.8), (16.2, -5.6)]), 0.9, INK)
    ex, ey = H(11.4, -2.0)
    if blink:
        f.ink(Hs([(9.8, -1.8), (13.0, -2.0)]), 0.9, INK)
    else:
        f.dot(ex, ey, 1.8, EYE_WHITE)
        ix, iy = H(11.9 + 0.4 * look_up, -2.0 - 0.2 * (1.0 - look_up))
        f.dot(ix, iy, 1.3, IRIS)
        f.dot(ix + 0.4, iy - 0.5, 0.45, K.WHITE)
        f.ink(Hs([(9.6, -3.4), (13.4, -3.8)]), 0.7, INK)
    # A flat nose at the top of the muzzle, and the long upper lip under it.
    f.ink(Hs([(16.6, -1.6), (20.0, 0.8)]), 0.7, SKIN_SHADE)
    f.dot(*H(20.4, 1.8), 0.8, INK)
    f.ink(Hs([(20.2, 3.0), (21.2, 5.6)]), 0.5, SKIN_SHADE)
    if mouth > 0.05:
        f.poly(Hs([(14.0, 7.0), (21.4, 6.6), (20.6, 7.0 + jaw * 0.8), (14.6, 7.4 + jaw * 0.6)]), MOUTH, body=False)
    f.ink(Hs([(13.6, 7.2), (21.6, 6.6)]), 0.8, INK)
    # The ear, small, far back on the side of the skull.
    _plate(f, Hs(K.ellipse_points(-4.0, 1.0, 2.0, 2.8, 14)), SKIN, edge=0.7, body=False)
    f.ink(Hs([(-4.0, -0.4), (-3.4, 1.6)]), 0.6, SKIN_SHADE)
    # Hair on the crown and at the back of the head.
    _tufts(f, Hs([(7.0, -8.0), (1.0, -12.0), (-6.0, -11.0), (-10.5, -6.0), (-11.5, 1.0), (-8.5, 7.0)]), FUR, 2.2)
    f.ink(Hs([(-6.0, -6.0), (-3.0, -8.4)]), 0.6, FUR_DARK)
    f.ink(Hs([(-8.0, -1.0), (-6.4, -4.2)]), 0.6, FUR_DARK)

    # -- the near leg -------------------------------------------------------------
    _leg(f, U(1.0, 3.0), ankle_of(-1.0, 3.0), FUR, FUR_DARK)

    # -- the near arm, with the stone ---------------------------------------------
    sh_near = U(-1.0, -38.0)
    if anim == "walk":
        near_hand = (sh_near[0] + 4.0 + 9.0 * stride, sh_near[1] + 45.0)
        angle = 92.0 + 18.0 * stride
    else:
        # Idle and talk: the stone held up in front, to look at or to show.
        near_hand = (sh_near[0] + 18.0 + 6.0 * show, sh_near[1] + 28.0 - 14.0 * show)
        angle = 20.0 - 30.0 * show
        if anim == "death":
            near_hand = (sh_near[0] + 10.0, sh_near[1] + 34.0)
            angle = 80.0
    _arm(f, sh_near, near_hand, FUR, FUR_DARK, angle=angle, grip=0.8, stone=anim != "death" or t < 0.4)
    if anim == "death" and t >= 0.4:
        # The stone, let go, on the ground in front of her.
        sx = cx + 30.0
        _plate(f, K.ellipse_points(sx, GROUND - 3.6, 4.6, 3.6, 18), STONE, edge=0.9)
    return f.finish(outline=INK, width=1.4)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
