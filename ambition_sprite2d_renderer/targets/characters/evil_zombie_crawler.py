"""Sprite generator for the Crawling Conscript: a Risen Conscript with no
legs, who drags himself along the floor on his arms (Jon, 2026-10-30: "maybe
the risen conscript had a variant where they are missing legs and crawl on
the ground with their arms").

He is the Risen Conscript's kin (``evil_zombie``) and wears that man's
pieces: the dead grey face, the dented helmet, the torn grey-green tunic, the
red armband (an invented cog, not a real symbol), the bare near forearm. His
legs end in two torn stumps of breeches under the hem of his tunic. He lies
on his belly, facing right, his head up and his arms out in front of him.

He is low and wide. The body the game moves is his body alone, on the floor:
his belly and his stumps are on the ground line in every row he does not
rise in. There is no drop shadow.

How he fights, as Hollow Knight's enemies do (notice, space, telegraph,
attack):

* ``notice``: he pushes his head and chest up on his arms and looks.
* ``windup``: he rears back on his far arm, his near arm up and back, his jaw
  open. This is the tell, and it is long.
* ``attack_side``: he throws himself forward along the floor, both arms out
  to grab, and bites; then he falls flat and lies there (the long recovery).

He is a person of ``_person_rig``.
"""

from __future__ import annotations

import math
from typing import List

from ._ai_era_kit import Point, lerp, mix, turned
from . import _person_rig as R
from . import evil_zombie as Z
from ._person_rig import Build, Person, Stamp, loop, shot

TARGET_NAME = "evil_zombie_crawler"
TARGET_BASENAME = TARGET_NAME
DISPLAY_NAME = "Crawling Conscript"

TRAITS = ["story", "humanoid", "enemy", "combatant", "authoritarian", "soldier", "undead", "zombie", "slow", "crawler"]

ACTOR_METADATA = {
    "actor": {"character_id": "npc_evil_zombie_crawler", "display_name": DISPLAY_NAME},
    "body": {"body_plan": "HumanoidBiped", "body_kind": "Standard", "mass_class": "Medium", "traits": TRAITS, "locomotion_hint": "Crawl"},
    "capabilities": {
        "traversal": {"walk": True, "jump": None, "climb": None, "fly": None, "swim": None, "crawl": True, "use_lifts": None, "door_access": []},
        "interactions": {"talk": False, "trade": None, "carry": None, "open_doors": []},
    },
    "brain": {"default_preset": "melee_brute_striker"},
    "actions": {"default_preset": "evil_crawler_lunge"},
    "visual": {"default_pose": "idle", "portrait": {"animation": "idle", "frame": 0}},
    "tags": TRAITS,
    "sockets": {},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "action.melee.primary": {
            "animation": "attack_side",
            "events": [
                {"t": 0.2, "event": "hitbox_active_start", "source": "explicit.profile.combat_humanoid"},
                {"t": 0.45, "event": "hitbox_active_end", "source": "explicit.profile.combat_humanoid"},
            ],
        },
        "combat.hurt": {"animation": "hit", "events": []},
        "combat.death": {"animation": "death", "events": []},
    },
    "authoring_description": (
        "A Risen Conscript with no legs: the same dead grey face, dented helmet, torn grey-green "
        "tunic and red armband (an invented cog; no real symbol), and two torn stumps of breeches. "
        "He lies on his belly and drags himself along the floor on his arms."
    ),
    "gameplay_description": (
        "A slow, low crawler. He lies still until you are close, rears back on one arm (a long "
        "tell), lunges along the floor to grab and bite, then lies flat and open for a while."
    ),
    "dialogue_hints": {"barks": ["*a scrape of nails on stone*", "Hhhh... re... port...", "*a wet drag*"]},
}

#: His body box: low and wide. ``height`` is the top of his raised head as he
#: lies (the idle row); his hips are behind the middle, his head in front.
BUILD = Build(hip_up=Z.BUILD.hip_up, thigh=Z.BUILD.thigh, shin=Z.BUILD.shin, neck=Z.BUILD.neck, upper=Z.BUILD.upper, fore=Z.BUILD.fore,
              near_shoulder=Z.BUILD.near_shoulder, far_shoulder=Z.BUILD.far_shoulder, near_hip=Z.BUILD.near_hip, far_hip=Z.BUILD.far_hip,
              head_up=Z.BUILD.head_up, throat=Z.BUILD.throat, height=44.0, half_width=(46.0, 40.0))

X = Person(TARGET_NAME, BUILD, frame=(256, 132), ground=120.0, cx=126.0)
K = X.K
P = X.P
U = X.U
assert K.scale == Z.K.scale, "he wears the conscript's pieces: one paint scale"

# ---- What he wears: the conscript's pieces ----------------------------------

X.torso = Z.X.torso
X.collar = Z.X.collar
X.neck = Z.X.neck
X.head_layers = Z.X.head_layers
X.upper_arm = Z.X.upper_arm
X.forearm = Z.X.forearm
X.hand = Z.X.hand
X.layers["front"] += list(Z.X.layers["front"])

#: His legs are gone a little under the hips: the stump is this part of a
#: thigh, and its torn end is there.
STUMP = 0.8
X.thigh = lambda near: [(0.0, STUMP, 9.4, 9.8, Z.BREECHES if near else Z.BREECHES_DARK)]
X.shin = lambda near: []
X.shoe = lambda near: None


def _torn_end(dark: bool):
    """The torn end of a stump of breeches: rags, and the dark in them."""
    colour = Z.BREECHES_DARK if dark else Z.BREECHES

    def shape(d) -> None:
        K.poly(d, [K.at(-1.0, -5.4), K.at(1.6, -5.0), K.at(3.6, -3.4), K.at(2.2, -1.8), K.at(4.4, -0.2), K.at(2.4, 1.2), K.at(3.8, 3.4),
                   K.at(1.0, 4.0), K.at(-1.0, 5.2)], (255, 255, 255, 255))

    def detail(d) -> None:
        K.oval(d, K.at(1.0, 0.0), 1.6, 3.2, mix(Z.STAIN, Z.SOCKET, 0.4))
        K.line(d, [K.at(2.0, -3.0), K.at(3.0, -1.6)], mix(colour, Z.UNIFORM_LIGHT, 0.5), 0.4)

    return K.solid(("torn_end", dark), shape, colour, detail, outline=1.0, rim=0.2, shade=0.3, shade_colour=Z.BREECHES_DARK)


def _stumps(ctx) -> List[Stamp]:
    """The torn end of each stump, turned along it. The far one goes under the
    tunic with its leg; the near one over it."""
    out: List[Stamp] = []
    for near in (False, True):
        root, knee = ctx.frame.legs[0 if near else 1][:2]
        end = (lerp(root[0], knee[0], STUMP), lerp(root[1], knee[1], STUMP))
        turn = math.degrees(math.atan2(knee[1] - root[1], knee[0] - root[0]))
        out.append((_torn_end(not near), end, "near_stump" if near else "far_stump", turn))
    return out


X.layers["under_torso"].append(_stumps)

# ---- How he lies -------------------------------------------------------------
#
# All of him is turned (``rot``) about his hips: 90 lays him on his belly with
# his head forward, less raises his chest (up on his arms). His hands are
# placed where they are in the frame (``wrists``): so far in front of the
# shoulder and so high off the floor, and a hand on the floor lies flat.

#: Where his hips lie: on the floor, his stumps out behind and down.
HIPS = (0.0, 26.6)
STUMPS = dict(nf=(12.0, 34.0, 0.0), ff=(9.0, 35.0, 0.0))


def _arm_to(pose: dict, near: bool, ahead: float, up: float, flat: bool) -> dict:
    """The arm keys that put the wrist ``ahead`` px in front of its shoulder
    and ``up`` px over the floor; ``flat``, the hand lies along the floor."""
    key = "na" if near else "fa"
    rot = float(pose["rot"])
    shoulder = X.arm_joints(pose, near)[0]
    target = (shoulder[0] + ahead, X.ground - up)
    local = turned(((target[0] - shoulder[0]) / U, (target[1] - shoulder[1]) / U), -rot)
    out = {key: local}
    if flat:
        elbow, wrist = X.arm_joints(dict(pose, **out), near)[1:]
        out[key[0] + "ht"] = 4.0 - math.degrees(math.atan2(wrist[1] - elbow[1], wrist[0] - elbow[0]))
    return out


def lying(lift: float = 0.0, *, slide: float = 0.0, near=(36.0, 4.0, True), far=(30.0, 4.0, True), **kw):
    """A pose of his on his belly. ``lift`` 0 is flat on the floor, 1 up on
    his arms; ``slide`` moves all of him forward (units). ``near`` and
    ``far``: each wrist as ``(ahead, up, flat)`` (``_arm_to``), or None to
    give the arm's keys in ``kw``."""
    rot = 88.0 - 34.0 * lift
    pose = dict(X.rest, rot=rot, hip=(HIPS[0], HIPS[1] - 4.0 * max(0.0, lift)), off=(-14.0 + slide, 0.0), lean=0.0, head=(0.0, 0.0, -rot + 10.0 - 6.0 * lift), arm="under", nab=-1.0,
                fab=-1.0, nh="flat", fh="flat", nht=0.0, fht=0.0, nf=(STUMPS["nf"][0] - 24.0 * lift, 34.0, 0.0), ff=(STUMPS["ff"][0] - 24.0 * lift, 35.0, 0.0))
    pose.update(kw)
    for is_near, where in ((True, near), (False, far)):
        if where is not None:
            pose.update(_arm_to(pose, is_near, *where))
    return pose


X.set_rest(**lying(0.12))


@X.row
def idle(i: int, n: int):
    # He lies with his head up, and it sways; his jaw works; his near hand
    # drags its nails a little on the floor.
    _, s, c = loop(i, n)
    return lying(0.12 + 0.03 * s, near=(36.0 - 2.0 * c, 4.0, True), far=(30.0, 4.0, True), head=(0.0, 0.0, -88.0 + 5.0 * c),
                 mouth="open" if i in (3, 4) else "flat")


def _pull(ph: float, reach: float):
    """One pull of an arm: it reaches out in front and up (``ph`` 0), comes
    down onto the floor, and drags back under his shoulder. ``(ahead, up,
    flat)``."""
    out = 0.5 + 0.5 * math.cos(ph)
    lifted = max(0.0, math.sin(ph))
    return (12.0 + reach * out, 4.0 + 9.0 * lifted, lifted < 0.2)


@X.row
def walk(i: int, n: int):
    # The crawl: one arm reaches, claws the floor and drags him up to it,
    # then the other. His chest comes up a little as an arm pulls.
    ph, s, c = loop(i, n)
    heave = abs(math.sin(ph))
    pose = lying(0.1 + 0.1 * heave, slide=1.0 * c, near=_pull(ph, 26.0), far=_pull(ph + math.pi, 22.0), head=(0.0, 0.0, -88.0 + 4.0 * s),
                 nf=(12.0 + 1.0 * c, 34.0, 0.0), ff=(9.0 - 1.0 * c, 35.0, 0.0), mouth="open" if i in (2, 7) else "flat")
    pose["nh"] = "open" if not _pull(ph, 0.0)[2] else "flat"
    pose["fh"] = "open" if not _pull(ph + math.pi, 0.0)[2] else "flat"
    return pose


@X.row
def run(i: int, n: int):
    return walk(i, n)


#: Down flat, as he lies.
LOW = lying(0.12)
#: Up on his arms, his head up, his eyes on you.
UP = lying(1.0, near=(6.0, 3.0, True), far=(2.0, 3.0, True), head=(0.0, 0.0, -56.0), eyes="wide", mouth="big")


@X.row
def notice(i: int, n: int):
    # He pushes himself up on his arms, his head comes up, his jaw drops,
    # and he looks.
    look = dict(UP, head=(0.0, 0.0, -50.0), mouth="open")
    return X.keys(shot(i, n), [(0.0, LOW), (0.35, UP, "snap"), (0.7, look), (1.0, look)], drag={"head": 0.1})


def _reared(shake: float = 0.0) -> dict:
    """Reared back on his far arm, his near arm up and back over him to claw."""
    return lying(0.85, slide=-6.0, near=(-16.0 + shake, 62.0 - shake, False), far=(4.0, 3.0, True), head=(0.0, 0.0, -50.0), eyes="wide",
                 mouth="big", arm="under", nh="open", nab=1.0, shrug=(0.0, -1.0))


REARED = _reared()


@X.row
def windup(i: int, n: int):
    # The tell: he rears back on his far arm and lifts his near arm high. It
    # shakes as he holds it.
    _, s, _c = loop(i, n)
    return _reared(1.0 * s)


#: Thrown forward along the floor, both arms out to grab, his teeth at you.
LUNGED = lying(0.25, slide=14.0, near=(36.0, 7.0, False), far=(32.0, 5.0, False), head=(0.0, 0.0, -80.0), nh="open", fh="open", mouth="big")
#: Flat on his face after it, his arms out in front.
SPENT = lying(0.0, slide=12.0, near=(32.0, 3.0, True), far=(28.0, 3.0, True), head=(0.0, 0.0, -92.0), eyes="closed", mouth="open")


@X.row
def attack_side(i: int, n: int):
    # From the reared tell he throws himself forward, grabs and bites, then
    # falls flat and lies there a while before he comes up again.
    bite = dict(LUNGED, mouth="grit", head=(0.0, 0.0, -76.0))
    return X.keys(shot(i, n), [(0.0, REARED), (0.16, LUNGED, "snap"), (0.28, bite), (0.4, LUNGED), (0.55, SPENT), (0.85, SPENT), (1.0, LOW)])


STRUCK = lying(0.45, slide=-4.0, near=(14.0, 9.0, False), far=(12.0, 3.0, True), head=(0.0, 0.0, -36.0), nh="open", eyes="wince", mouth="big")


@X.row
def hit(i: int, n: int):
    # His head snaps back and his chest comes up off the floor, late.
    return X.keys(shot(i, n), [(0.0, LOW), (0.25, STRUCK), (0.55, STRUCK), (1.0, LOW)], drag={"head": 0.12})


#: Still on the floor, face down, his arms out in front and to his sides.
DEAD = lying(-0.04, slide=2.0, near=(22.0, 2.0, True), far=(30.0, 2.0, True), head=(0.0, 0.0, -96.0), eyes="dead", mouth="open")


@X.row
def death(i: int, n: int):
    # He comes up once on his arms, and they give; he falls flat.
    up = lying(0.6, near=(10.0, 3.0, True), far=(6.0, 3.0, True), head=(0.0, 0.0, -46.0), nh="open", eyes="wince", mouth="big")
    return X.keys(shot(i, n), [(0.0, STRUCK), (0.3, up), (0.6, DEAD, "in"), (1.0, DEAD)])


@X.row
def death_idle(i: int, n: int):
    twitch = 2.0 if i == n - 2 else 0.0
    return lying(-0.04, slide=2.0, near=(22.0, 2.0 + twitch, True), far=(30.0, 2.0, True), head=(0.0, 0.0, -96.0), eyes="dead", mouth="open")


X.rows = [("idle", 8, 170), ("walk", 10, 120), ("run", 10, 90), ("notice", 8, 90), ("windup", 6, 90), ("attack_side", 12, 80), ("hit", 5, 100),
          ("death", 8, 130), ("death_idle", 8, 220)]

# ---- What his blows do -------------------------------------------------------


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    anim, u = ctx.anim, ctx.u
    if anim == "attack_side" and 0.2 <= u <= 0.4 and ctx.pose["mouth"] == "grit":
        tip: Point = (ctx.head[0] + 11.0, ctx.head[1] + 5.0)
        out.append((R.burst(K, 7.0, Z.IMPACT, Z.IMPACT_DARK, 8), tip, "bite", 0.0))
    if anim == "attack_side" and 0.4 <= u <= 0.62:
        # Dust where he slaps down onto the floor.
        out.append((R.dust(K, 3.6, Z.DUST, Z.DUST_DARK), (ctx.hand[0] + 4.0, ctx.ground - 3.0), "dust_ahead", 0.0))
        out.append((R.dust(K, 3.0, Z.DUST, Z.DUST_DARK), (ctx.hip[0] - 6.0, ctx.ground - 3.0), "dust_behind", 0.0))
    elif anim == "hit" and u <= 0.5:
        out.append((R.burst(K, 9.0, Z.IMPACT, Z.IMPACT_DARK, 8), (ctx.head[0] + 10.0, ctx.head[1] - 2.0), "struck", 0.0))
    elif anim == "death" and 0.55 <= u <= 0.85:
        out.append((R.dust(K, 4.0, Z.DUST, Z.DUST_DARK), (ctx.head[0] + 6.0, ctx.ground - 3.0), "dust_ahead", 0.0))
    return out


X.effects = _effects

ROWS = X.rows
FRAME_SIZE = X.frame
_render_frame = X.render_frame
render, main, render_canonical = R.entry_points(X, ACTOR_METADATA, DISPLAY_NAME)


def render_portraits(out_dir, **opts):
    """His portraits are frames of this sheet: his head as he lies."""
    del opts
    return X.portraits(out_dir, {"default": ("idle", (1,), 0, False), "talking": ("notice", (2, 3, 4, 5, 6, 7), 120, True)}, view_width=44.0)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}

if __name__ == "__main__":
    raise SystemExit(main())
