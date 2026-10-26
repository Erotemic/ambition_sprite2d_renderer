"""Sprite generator for the Evil Heavy: the iron trooper of Godwin Castle.

The look (2026-10-15, Jon's pick of a baddie): a big, broad man of about 205
cm, seen three quarters from the front and facing right. Riveted iron plate
over the grey-green uniform of the regime: a breastplate, a plate on his
near shoulder, plates on his arms and shins, a gorget, iron gauntlets. An
iron helmet that hides all his face: a round dome with a ridge, a face plate
with one dark slit for his eyes and holes to breathe through, a straight
guard over his neck. The shape is invented; it is not a copy of a helmet of
a real army. The red armband of the regime is over the plate of his near
arm (``_evil_faction``: an invented cog, not a real symbol). Heavy boots.

He carries a chain gun, but nothing he carries is in this drawing: the gun
is the prop ``evil_chain_gun``, and the runtime held-item system draws it.
Here his gauntlets are empty and closed in a grip for a gun held at the
hip: his near (rear) hand on its grip, his far hand forward under it.

His rows: ``shoot`` (braced, the gun shakes him), ``slash`` (he drives the
gun forward with both hands, butt first), ``attack_down`` (both fists into
the floor). There is no drop shadow.

He is a person of ``_person_rig``.
"""

from __future__ import annotations

import math
from typing import List

from ._ai_era_kit import OUTLINE, WHITE, RGBA, lerp, mix
from . import _evil_faction as F
from . import _person_rig as R
from ._person_rig import Build, Person, Stamp, loop, shot

TARGET_NAME = "evil_heavy"
TARGET_BASENAME = TARGET_NAME
DISPLAY_NAME = "Iron Trooper"

TRAITS = ["story", "humanoid", "enemy", "combatant", "authoritarian", "soldier", "heavy", "armored", "gunner"]

ACTOR_METADATA = {
    "actor": {"character_id": "npc_evil_heavy", "display_name": DISPLAY_NAME},
    "body": {"body_plan": "HumanoidBiped", "body_kind": "Wide", "mass_class": "Heavy", "traits": TRAITS, "locomotion_hint": "Walk"},
    "capabilities": {
        "traversal": {"walk": True, "jump": True, "climb": None, "fly": None, "swim": None, "crawl": None, "use_lifts": True,
                      "door_access": ["public"]},
        "interactions": {"talk": False, "trade": None, "carry": None, "open_doors": ["public"]},
    },
    "brain": {"default_preset": "skirmisher_ranger"},
    "actions": {"default_preset": "ranger_arrow"},
    "visual": {"default_pose": "idle", "portrait": {"animation": "idle", "frame": 0}},
    "tags": TRAITS,
    "sockets": {},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "action.ranged.primary": {"animation": "shoot", "events": [{"t": 0.0, "event": "projectile_release", "source": "explicit.profile.combat_humanoid"}]},
        "action.melee.primary": {
            "animation": "slash",
            "events": [
                {"t": 0.4, "event": "hitbox_active_start", "source": "explicit.profile.combat_humanoid"},
                {"t": 0.62, "event": "hitbox_active_end", "source": "explicit.profile.combat_humanoid"},
            ],
        },
        "combat.hurt": {"animation": "hit", "events": []},
        "combat.death": {"animation": "death", "events": []},
    },
    "authoring_description": (
        "A heavy trooper of the Evil dimension's regime: riveted iron plate over the grey-green "
        "uniform, an iron helmet with one slit for his eyes (an invented shape), the red armband "
        "with the faction's invented cog over the plate of his arm. His hands are empty in a "
        "two-handed grip; his chain gun is the held prop `evil_chain_gun`."
    ),
    "gameplay_description": "A slow, armored gunner: he braces and fires, drives the gun into you, and pounds the floor.",
    "dialogue_hints": {"barks": ["Iron obeys.", "Hold still. It is easier for both of us.", "The order is heavy. I carry it."]},
}

UNIFORM: RGBA = (98, 110, 92, 255)
UNIFORM_DARK: RGBA = (66, 76, 64, 255)
IRON: RGBA = (118, 124, 134, 255)
IRON_DARK: RGBA = (78, 82, 94, 255)
IRON_DEEP: RGBA = (50, 52, 62, 255)
IRON_LIGHT: RGBA = (176, 182, 192, 255)
RIVET: RGBA = (204, 206, 210, 255)
BOOT: RGBA = (48, 44, 50, 255)
BOOT_DARK: RGBA = (28, 26, 32, 255)
SOLE: RGBA = (20, 18, 22, 255)
BELT: RGBA = (36, 30, 30, 255)
SLIT: RGBA = (16, 12, 16, 255)
GLINT: RGBA = (226, 76, 60, 255)
SPARK: RGBA = (255, 238, 184, 255)
SPARK_DARK: RGBA = (214, 122, 58, 255)
DUST: RGBA = (196, 186, 170, 255)
DUST_DARK: RGBA = (122, 112, 102, 255)

#: 205 cm, and broad. ``height`` is the top of his helmet (measured on the
#: idle row).
BUILD = Build(hip_up=58.0, thigh=28.6, shin=27.4, neck=(0.4, -43.0), upper=22.5, fore=21.5, near_shoulder=(-8.0, -38.0), far_shoulder=(9.0, -37.6),
              near_hip=(-5.0, 0.0), far_hip=(5.0, 0.0), ankle_up=3.6, head_up=(1.6, -14.6), throat=(0.0, 4.4), height=129.0, half_width=(18.0, 20.0))

X = Person(TARGET_NAME, BUILD, frame=(256, 208), ground=194.0, cx=120.0)
K = X.K
P = X.P
TOP = BUILD.neck[1] - 2.0


def rivets(d, pts, r: float = 0.75) -> None:
    for p in pts:
        K.oval(d, p, r, r, RIVET, OUTLINE, 0.3)


# ---- The trunk ---------------------------------------------------------------


def _plate(d, hb: float, hf: float) -> None:
    """The breastplate over his tunic, the belt, and the skirt of the
    tunic under it."""
    del hb
    # The tunic under the plate, from the belt down.
    K.poly(d, [K.at(-40.0, -5.0), K.at(40.0, -5.0), K.at(40.0, 30.0), K.at(-40.0, 30.0)], UNIFORM)
    K.line(d, [K.at(9.0, -4.0), K.at(9.6 + hf * 0.4, 13.0)], UNIFORM_DARK, 0.6)
    K.line(d, [K.at(-40.0, 12.4), K.at(40.0, 12.4)], UNIFORM_DARK, 0.6)
    # The plate: a ridge down its middle, a lame at its foot, rivets.
    K.line(d, [K.at(6.4, TOP + 3.0), K.at(8.4, -22.0), K.at(7.6, -10.0)], IRON_LIGHT, 0.9)
    K.line(d, [K.at(-40.0, -14.0), K.at(40.0, -14.4)], IRON_DEEP, 0.7)
    K.line(d, [K.at(-40.0, -13.2), K.at(40.0, -13.6)], IRON_LIGHT, 0.4)
    rivets(d, [K.at(x, TOP + 4.0 + 0.1 * x) for x in (-8.0, -3.0, 2.0, 7.0)] + [K.at(x, -11.0) for x in (-8.0, -3.0, 2.0, 7.0)])
    # The belt.
    K.poly(d, [K.at(-40.0, -9.0), K.at(40.0, -9.0), K.at(40.0, -4.6), K.at(-40.0, -4.6)], BELT)
    K.rrect(d, 7.2, -9.6, 11.6, -4.0, 0.6, IRON_LIGHT, OUTLINE, 0.4)


X.torso = R.make_torso(K, ("evil_heavy",), IRON, IRON_DARK, back=(14.6, 15.0, 13.0, 14.0), front=(14.2, 14.6, 13.6, 14.6), hem_y=13.0, top=TOP,
                       shoulders=((-7.0, -38.0), (8.0, -37.6)), shoulder_r=(9.0, 8.4), neck=(-6.0, 6.0), shade_from=10.0, detail=_plate)


def _gorget():
    """The iron collar round his neck, from its base."""

    def shape(d) -> None:
        K.poly(d, [K.at(-7.4, 2.0), K.at(-7.0, -4.0), K.at(0.0, -5.4), K.at(7.4, -4.6), K.at(8.4, 2.0)], WHITE)

    def detail(d) -> None:
        K.line(d, [K.at(-7.0, -1.4), K.at(0.0, -2.6), K.at(8.0, -1.8)], IRON_DEEP, 0.6)
        rivets(d, [K.at(-3.6, -3.4), K.at(4.4, -3.4)], 0.6)

    return K.solid(("gorget",), shape, IRON, detail, outline=1.2, rim=0.35, shade=0.35, shade_colour=IRON_DEEP)


X.collar = _gorget
X.neck = R.make_neck(K, IRON_DEEP, 8.0)

# ---- The helmet --------------------------------------------------------------


def _helmet():
    """His helmet, from the middle of his head: a dome with a ridge, a face
    plate with one slit and holes to breathe, a straight guard behind."""

    def shape(d) -> None:
        K.oval(d, K.at(0.0, -3.0), 10.0, 10.4, WHITE)
        K.rrect(d, K.home[0] - 10.0, K.home[1] - 4.0, K.home[0] - 2.0, K.home[1] + 10.4, 1.4, WHITE)
        K.poly(d, [K.at(0.0, -8.0), K.at(9.6, -7.0), K.at(11.6, -1.0), K.at(11.0, 7.0), K.at(7.0, 11.4), K.at(0.0, 11.0)], WHITE)

    def detail(d) -> None:
        # The face plate is a darker iron than the dome.
        K.poly(d, [K.at(1.6, -6.4), K.at(20.0, -6.4), K.at(20.0, 20.0), K.at(1.6, 20.0)], mix(IRON, IRON_DARK, 0.4))
        K.line(d, [K.at(1.6, -6.4), K.at(1.8, 11.0)], IRON_DEEP, 0.6)
        # The ridge over the dome, and the band at its foot.
        K.line(d, [K.at(-9.0, -7.0), K.at(-3.0, -12.4), K.at(4.0, -12.4), K.at(9.6, -7.4)], IRON_LIGHT, 1.0)
        K.line(d, [K.at(-11.0, -4.4), K.at(1.6, -5.6)], IRON_DEEP, 0.7)
        rivets(d, [K.at(-8.4, -4.4), K.at(-4.4, -4.8), K.at(-0.6, -5.2), K.at(-6.0, 7.6)], 0.65)
        # The slit for his eyes, and a red glint in it.
        K.poly(d, [K.at(3.6, -2.6), K.at(12.0, -2.4), K.at(12.0, 0.2), K.at(3.6, 0.0)], SLIT)
        K.oval(d, K.at(8.6, -1.2), 1.1, 0.7, GLINT)
        # The holes to breathe.
        for x, y in ((6.0, 4.0), (8.4, 4.0), (6.0, 6.4), (8.4, 6.4), (10.4, 5.2)):
            K.oval(d, K.at(x, y), 0.55, 0.55, SLIT)

    return K.solid(("helmet",), shape, IRON, detail, outline=1.3, rim=0.4, shade=0.35, shade_colour=IRON_DEEP)


X.head_layers = lambda pose: [(_helmet(), "helmet")]

# ---- The limbs ---------------------------------------------------------------

# Plate on the upper arm and a vambrace on the forearm, over his sleeves.
X.upper_arm = lambda near: [(0.0, 1.0, 10.6, 9.2, UNIFORM if near else UNIFORM_DARK)]
X.forearm = lambda near: [(0.0, 0.24, 8.6, 8.2, UNIFORM if near else UNIFORM_DARK), (0.2, 1.0, 9.4, 8.6, IRON if near else IRON_DARK)]
X.thigh = lambda near: [(0.0, 1.0, 11.0, 9.0, UNIFORM if near else UNIFORM_DARK)]
X.shin = lambda near: [(0.0, 0.16, 9.0, 8.6, UNIFORM if near else UNIFORM_DARK), (0.12, 1.0, 10.2, 8.4, IRON if near else IRON_DARK),
                       (0.2, 0.9, 1.6, 1.2, IRON_LIGHT if near else IRON)]
X.hand = R.make_hand(K, IRON_DARK, IRON_DEEP, SOLE, IRON, IRON_DARK, size=1.35)
X.shoe = R.make_shoe(K, BOOT, BOOT_DARK, BUILD.ankle_up, long=1.3, sole=SOLE, heel=1.0)


def _pauldron():
    """The plate over his near shoulder, along +x (down his arm) from the
    top of his arm."""

    def shape(d) -> None:
        K.poly(d, [K.at(-5.0, -7.4), K.at(5.0, -8.6), K.at(12.0, -7.4), K.at(13.0, 0.0), K.at(12.0, 7.4), K.at(5.0, 8.6), K.at(-5.0, 7.4), K.at(-7.4, 0.0)], WHITE)

    def detail(d) -> None:
        for x in (6.0, 10.0):
            K.line(d, [K.at(x, -8.0), K.at(x + 0.8, 0.0), K.at(x, 8.0)], IRON_DEEP, 0.6)
        K.line(d, [K.at(-4.0, -5.0), K.at(4.0, -6.4)], IRON_LIGHT, 0.7)
        rivets(d, [K.at(-2.4, -4.4), K.at(-2.4, 4.4), K.at(-4.6, 0.0)], 0.65)

    return K.solid(("pauldron",), shape, IRON, detail, outline=1.2, rim=0.4, shade=0.35, shade_colour=IRON_DEEP)


def _knee():
    def shape(d) -> None:
        K.oval(d, K.home, 5.2, 5.6, WHITE)

    def detail(d) -> None:
        rivets(d, [K.at(0.0, 0.0)], 0.7)

    return K.solid(("knee",), shape, IRON, detail, outline=1.1, rim=0.4, shade=0.35, shade_colour=IRON_DEEP)


def _near_plates(ctx) -> List[Stamp]:
    """His near shoulder plate, the band over his arm, and his knee plate."""
    out: List[Stamp] = [(_knee(), ctx.knee, "knee_plate", 0.0)]
    if ctx.pose["arm"] == "under":
        return out
    turn = math.degrees(math.atan2(ctx.elbow[1] - ctx.shoulder[1], ctx.elbow[0] - ctx.shoulder[0]))
    t = 0.5
    at = (lerp(ctx.shoulder[0], ctx.elbow[0], t), lerp(ctx.shoulder[1], ctx.elbow[1], t))
    out += [(_pauldron(), ctx.shoulder, "pauldron", turn), (F.band(K, 11.0, 6.4), at, "armband", turn), (F.emblem(K, 2.8), at, "armband_emblem", 0.0)]
    return out


X.layers["front"].append(_near_plates)

# ---- How he stands -----------------------------------------------------------

#: His hands in the grip of a gun at his hip: the near hand on its grip, the
#: far hand forward under it.
GRIP_NEAR = (9.0, 15.0)
GRIP_FAR = (12.0, 11.0)
X.set_rest(lean=2.0, na=GRIP_NEAR, fa=GRIP_FAR, nh="fist", fh="fist", nf=(-7.0, 0.0, 0.0), ff=(8.0, 0.0, 0.0), mouth="flat", brows=-1.0)


def _grip(dx: float = 0.0, dy: float = 0.0) -> dict:
    return {"na": (GRIP_NEAR[0] + dx, GRIP_NEAR[1] + dy), "fa": (GRIP_FAR[0] + dx, GRIP_FAR[1] + dy)}


@X.row
def idle(i: int, n: int):
    _, s, _c = loop(i, n)
    return P(hip=(0.0, 0.5 + 0.5 * s), lean=2.0 + 0.5 * s, head=(0.2, -0.2 * s, 1.0 * s), **_grip(0.0, -0.5 * s))


@X.row
def walk(i: int, n: int):
    # Slow and heavy: each boot comes down, and all of him with it.
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 7.5, 3.4)
    return P(hip=(0.5, 1.6 * abs(math.cos(ph))), lean=3.0 + 1.0 * c, head=(0.2, 0.0, 1.0 * s), nf=nf, ff=ff, hem=(1.0 + abs(c), 0.5 + abs(c)),
             **_grip(0.0, 1.2 * abs(math.cos(ph))))


@X.row
def run(i: int, n: int):
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 11.0, 7.0, 0.0)
    return P(hip=(2.0, 1.8 + 1.8 * math.cos(2.0 * ph)), lean=12.0, head=(0.4, 0.0, -6.0), nf=nf, ff=ff, hem=(4.0, 1.0), **_grip(1.0, -1.0 + 1.5 * s))


RISE = P(hip=(0.0, -2.0), lean=4.0, head=(0.0, 0.0, -4.0), nf=(-4.0, -11.0, 24.0), ff=(7.0, -14.0, 10.0), hem=(1.0, 2.0), **_grip(0.0, -3.0))
APEX = P(hip=(0.0, -2.0), lean=2.0, nf=(-4.0, -8.0, 18.0), ff=(8.0, -11.0, 6.0), hem=(2.0, 3.0), **_grip(0.0, -2.0))
FALL = P(hip=(0.0, -3.0), lean=-3.0, head=(0.0, 0.0, 4.0), nf=(-7.0, -4.0, 20.0), ff=(7.0, -8.0, 8.0), hem=(4.0, 4.0), **_grip(-1.0, -5.0))


@X.row
def jump(i: int, n: int):
    wind = P(hip=(-1.0, 11.0), lean=12.0, nf=(-7.0, 0.0, 0.0), ff=(8.0, 0.0, 0.0), **_grip(1.0, 3.0))
    return X.keys(shot(i, n), [(0.0, wind), (0.3, RISE), (0.6, RISE), (1.0, APEX)])


@X.row
def fall(i: int, n: int):
    _, s, _c = loop(i, n)
    return dict(FALL, nf=(-7.0, -4.0 + 1.5 * s, 20.0), ff=(7.0, -8.0 - 1.5 * s, 8.0))


LANDED = P(hip=(0.0, 16.0), lean=20.0, head=(1.0, 1.0, 4.0), nf=(-9.0, 0.0, 0.0), ff=(9.0, 0.0, 0.0), hem=(4.0, 3.0), **_grip(2.0, 6.0))


@X.row
def land_hard(i: int, n: int):
    return X.keys(shot(i, n), [(0.0, FALL), (0.2, LANDED), (0.6, LANDED), (1.0, X.full(P()))])


#: Braced to fire: feet wide, his weight forward, the gun up a little.
BRACED = P(hip=(-1.0, 4.0), lean=6.0, head=(0.4, 0.4, 2.0), nf=(-11.0, 0.0, 0.0), ff=(11.0, 0.0, 0.0), **_grip(1.0, -3.0))


@X.row
def shoot(i: int, n: int):
    # Each shot pushes him back and the gun up; he leans into it again.
    kick = 1.0 if i % 2 == 0 else 0.0
    return dict(BRACED, hip=(-1.0 - 1.2 * kick, 4.0 + 0.4 * kick), lean=6.0 - 2.0 * kick, head=(0.4 - 0.4 * kick, 0.4, 2.0 - 2.0 * kick),
                **_grip(1.0 - 1.6 * kick, -3.0 - 1.2 * kick))


@X.row
def slash(i: int, n: int):
    # Both hands drive the gun forward, butt first: up across his chest,
    # then out into you with all his weight.
    wind = P(hip=(-3.0, 3.0), lean=-6.0, head=(0.0, 0.0, -2.0), na=(3.0, 0.0), fa=(4.0, -4.0), nf=(-9.0, 0.0, 0.0), ff=(9.0, 0.0, 0.0))
    drive = P(hip=(6.0, 5.0), lean=18.0, head=(1.0, 1.0, 4.0), na=(20.0, 6.0), fa=(24.0, 2.0), nf=(-11.0, 0.0, 14.0), ff=(13.0, 0.0, 0.0), hem=(5.0, 1.0))
    return X.keys(shot(i, n), [(0.0, X.full(P())), (0.3, wind), (0.5, drive), (0.75, drive), (1.0, X.full(P()))])


#: Both fists high over his helmet.
RAISED = P(hip=(-1.0, 0.0), lean=-10.0, head=(-0.6, 0.6, 6.0), na=(7.0, -27.0), nab=-1.0, fa=(5.0, -27.0), fab=-1.0, arm="over", nf=(-9.0, 0.0, 0.0),
           ff=(9.0, 0.0, 0.0))
#: Both fists in the floor in front of him.
POUND = P(hip=(3.0, 15.0), lean=34.0, head=(2.0, 2.0, -8.0), na=(19.0, 22.0), fa=(18.0, 24.0), nf=(-10.0, 0.0, 0.0), ff=(10.0, 0.0, 0.0), hem=(5.0, 3.0))


@X.row
def attack_down(i: int, n: int):
    return X.keys(shot(i, n), [(0.0, X.full(P())), (0.3, RAISED), (0.42, dict(RAISED, lean=-13.0)), (0.55, POUND), (0.82, POUND), (1.0, X.full(P()))])


STRUCK = P(hip=(-3.0, 2.0), lean=-14.0, head=(-1.4, 0.0, -10.0), na=(6.0, 16.0), fa=(14.0, 12.0), nh="open", fh="open", nf=(-8.0, 0.0, 0.0),
           ff=(8.0, -4.0, -18.0), off=(-2.0, 0.0), hem=(0.0, 4.0))


@X.row
def hit(i: int, n: int):
    return X.keys(shot(i, n), [(0.0, X.full(P())), (0.25, STRUCK), (0.6, STRUCK), (1.0, X.full(P(lean=-2.0)))])


#: On his back, his boots up.
SUPINE = P(rot=-90.0, hip=(-2.0, 25.5), off=(13.0, 0.0), head=(0.0, 0.0, 0.0), na=(5.0, 14.0), fa=(2.0, 12.0), nh="open", fh="open",
           nf=(-4.5, 25.0, 0.0), ff=(4.5, 25.0, -10.0), lean=0.0)


@X.row
def death(i: int, n: int):
    sag = P(hip=(-4.0, 12.0), lean=-16.0, head=(-1.0, 0.0, -8.0), na=(8.0, 18.0), fa=(13.0, 14.0), nh="open", fh="open", nf=(-4.0, 0.0, 0.0),
            ff=(10.0, 0.0, -10.0), off=(-3.0, 0.0), hem=(0.0, 3.0))
    toppling = X.blend(sag, SUPINE, 0.5)
    toppling = dict(toppling, off=(toppling["off"][0], toppling["off"][1] - 6.0))
    return X.keys(shot(i, n), [(0.0, STRUCK), (0.3, sag), (0.46, toppling), (0.62, SUPINE), (1.0, SUPINE)])


X.rows = [("idle", 8, 160), ("walk", 8, 120), ("run", 8, 85), ("jump", 6, 100), ("fall", 6, 100), ("land_hard", 6, 90), ("shoot", 6, 60),
          ("slash", 8, 85), ("attack_down", 10, 85), ("hit", 5, 95), ("death", 8, 120)]

# ---- What his blows do -------------------------------------------------------


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    anim, u = ctx.anim, ctx.u
    if anim == "slash" and 0.45 <= u <= 0.72:
        out.append((R.burst(K, 11.0 if u < 0.6 else 8.0, SPARK, SPARK_DARK, 8), (ctx.far_hand[0] + 12.0, ctx.far_hand[1]), "drive_hit", 0.0))
    elif anim == "attack_down" and 0.5 <= u <= 0.88:
        late = u > 0.7
        at = ((ctx.hand[0] + ctx.far_hand[0]) / 2.0 + 4.0, ctx.ground - 10.0)
        out.append((R.burst(K, 10.0 if late else 14.0, DUST, DUST_DARK, 10), at, "ground_hit", 0.0))
        out.append((R.dust(K, 3.6 if late else 5.0, DUST, DUST_DARK), (at[0] + (20.0 if late else 13.0), ctx.ground - 4.0), "dust_ahead", 0.0))
        out.append((R.dust(K, 3.2 if late else 4.4, DUST, DUST_DARK), (at[0] - (18.0 if late else 12.0), ctx.ground - 3.0), "dust_behind", 0.0))
    elif anim == "hit" and u <= 0.5:
        out.append((R.burst(K, 11.0, SPARK, SPARK_DARK, 8), (ctx.head[0] + 12.0, ctx.head[1] - 2.0), "struck", 0.0))
    return out


X.effects = _effects

ROWS = X.rows
FRAME_SIZE = X.frame
_render_frame = X.render_frame
render, main, render_canonical = R.entry_points(X, ACTOR_METADATA, DISPLAY_NAME)


def render_portraits(out_dir, **opts):
    """His portraits are frames of this sheet."""
    del opts
    return X.portraits(out_dir, {"default": ("idle", (1,), 0, False), "talking": ("idle", (0, 1, 2, 3, 4, 5), 130, True)}, view_width=36.0)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}

# ---- In the round (``_round_cast``) --------------------------------------------
#
# His trunk in 3D comes from the numbers of his own maker (``auto_trunk``);
# his helmet from the side and from the front is drawn as his own helmet is
# drawn (``_helmet``), in the numbers of those views; the plates of his near
# arm and knee are his own pieces, put on the limbs of his stance. His rows
# do not use this.

import numpy as np  # noqa: E402

from . import _person_round as O  # noqa: E402
from . import _round_cast as C  # noqa: E402
from . import _round_wear as W  # noqa: E402


def _side_helmet():
    """His helmet from the side, from the middle of his head: the dome, the
    guard straight down behind, the face plate in front with its slit."""

    def shape(d) -> None:
        K.oval(d, K.at(-1.0, -3.0), 10.8, 10.4, WHITE)
        K.rrect(d, K.home[0] - 12.0, K.home[1] - 4.0, K.home[0] - 3.0, K.home[1] + 10.4, 1.4, WHITE)
        K.poly(d, [K.at(1.0, -8.0), K.at(10.6, -7.0), K.at(12.4, -1.0), K.at(11.8, 7.0), K.at(8.0, 11.4), K.at(1.0, 11.0)], WHITE)

    def detail(d) -> None:
        K.poly(d, [K.at(3.0, -6.4), K.at(20.0, -6.4), K.at(20.0, 20.0), K.at(3.0, 20.0)], mix(IRON, IRON_DARK, 0.4))
        K.line(d, [K.at(3.0, -6.4), K.at(3.2, 11.0)], IRON_DEEP, 0.6)
        K.line(d, [K.at(-11.0, -6.0), K.at(-4.0, -13.0), K.at(4.0, -12.8), K.at(10.4, -7.4)], IRON_LIGHT, 1.0)
        K.line(d, [K.at(-12.0, -4.4), K.at(3.0, -5.6)], IRON_DEEP, 0.7)
        rivets(d, [K.at(-9.4, -4.4), K.at(-5.4, -4.8), K.at(-1.6, -5.2), K.at(-7.4, 7.6)], 0.65)
        K.poly(d, [K.at(5.6, -2.6), K.at(12.8, -2.4), K.at(12.8, 0.2), K.at(5.6, 0.0)], SLIT)
        K.oval(d, K.at(10.2, -1.2), 1.0, 0.7, GLINT)
        for x, y in ((7.4, 4.0), (9.8, 4.0), (7.4, 6.4), (9.8, 6.4), (11.4, 5.2)):
            K.oval(d, K.at(x, y), 0.55, 0.55, SLIT)

    return K.solid(("helmet_side",), shape, IRON, detail, outline=1.3, rim=0.4, shade=0.35, shade_colour=IRON_DEEP)


def _front_helmet():
    """His helmet from the front: the dome with its ridge, the guard out at
    each side, the face plate with its slit and the red glint in it."""

    def shape(d) -> None:
        K.oval(d, K.at(0.0, -3.0), 10.6, 10.4, WHITE)
        K.poly(d, [K.at(-11.4, -2.0), K.at(-11.8, 9.6), K.at(-6.0, 11.4), K.at(6.0, 11.4), K.at(11.8, 9.6), K.at(11.4, -2.0)], WHITE)

    def detail(d) -> None:
        for sx in (-1.0, 1.0):
            K.poly(d, [K.at(8.4 * sx, -4.0), K.at(20.0 * sx, -4.0), K.at(20.0 * sx, 20.0), K.at(8.4 * sx, 20.0)], IRON_DARK)
        K.rrect(d, K.home[0] - 7.4, K.home[1] - 6.4, K.home[0] + 7.4, K.home[1] + 11.0, 1.6, mix(IRON, IRON_DARK, 0.4), IRON_DEEP, 0.6)
        K.line(d, [K.at(0.0, -13.4), K.at(0.0, -6.6)], IRON_LIGHT, 1.0)
        K.line(d, [K.at(-10.6, -5.2), K.at(0.0, -6.0), K.at(10.6, -5.2)], IRON_DEEP, 0.7)
        rivets(d, [K.at(x, -5.4 - 0.004 * x * x) for x in (-8.6, -4.4, 4.4, 8.6)], 0.65)
        K.poly(d, [K.at(-6.0, -2.6), K.at(6.0, -2.6), K.at(6.0, 0.2), K.at(-6.0, 0.2)], SLIT)
        K.oval(d, K.at(2.6, -1.2), 1.0, 0.7, GLINT)
        for x, y in ((-2.4, 4.0), (0.0, 4.0), (2.4, 4.0), (-1.2, 6.4), (1.2, 6.4)):
            K.oval(d, K.at(x, y), 0.55, 0.55, SLIT)

    return K.solid(("helmet_front",), shape, IRON, detail, outline=1.3, rim=0.4, shade=0.35, shade_colour=IRON_DEEP)


#: His helmet in 3D, for the views from behind: the dome, the face plate a
#: darker iron, the guard over his neck, the ridge, the band and the slit.
_DOME = ((0.0, -3.0, -0.4), (10.2, 10.4, 10.2))
HELMET_3D = O.Head3D(
    skin=IRON, shade=IRON_DARK, deep=IRON_DEEP, skull=_DOME, jaw=((0.0, 4.6, 3.0), (7.4, 6.4, 5.6)), nose=((0.0, 3.0, 8.0), (0.6, 0.6, 0.6)), ear=None,
    eye=(24.0, -1.2), eye_size=0.5, ink=GLINT,
    hair=lambda u, v: (np.abs(u) < 62.0) & (v > -6.2), hair_colour=mix(IRON, IRON_DARK, 0.4), hair_shade=IRON_DARK,
    volumes=[((0.0, 4.2, -5.6), (9.6, 7.0, 5.6))],
    lines=[O.curve([O.on_ellipsoid(*_DOME, u, v, 0.2)[0] for u, v in ((0.0, -9.0), (0.0, -12.6), (180.0, -12.6), (180.0, -9.0))], IRON_LIGHT, 1.0),
           O.curve([O.on_ellipsoid(*_DOME, u, -5.6, 0.2)[0] for u in range(-180, 181, 30)], IRON_DEEP, 0.7),
           O.curve([O.on_ellipsoid(*_DOME, u, -1.2, 0.3)[0] for u in (-40.0, -20.0, 0.0, 20.0, 40.0)], SLIT, 1.4)])

#: How he stands in the round: his hands in the grip of the gun at his hip,
#: as at rest (the gun is the held prop, not drawn here).
STANCE = C.Stance(hands={"r": C.Hand(l=-4.0, pole=(-0.6, 0.2, -1.0), mode="fist"), "l": C.Hand(l=4.0, pole=(0.6, 0.2, -1.0), mode="fist")}, stagger=2.4)
BODY = C.PersonBody(X, heads={"side": lambda pose: [(_side_helmet(), "helmet")], "front": lambda pose: [(_front_helmet(), "helmet")]})

# Where his near arm and knee are in that stance, for the plates on them.
_J = BODY.joints(STANCE.stagger)
_ELBOW, _ = O.two_bone(_J.shoulders["r"], _J.wrist(True, -4.0), BUILD.upper, BUILD.fore, (-0.6, 0.2, -1.0))
_KNEE, _ = O.two_bone(_J.hips["r"], _J.ankles["r"], BUILD.thigh, BUILD.shin, (0.0, 0.0, 1.0))
_SHOULDER = np.asarray(_J.shoulders["r"])
_BAND = tuple(_SHOULDER + 0.5 * (np.asarray(_ELBOW) - _SHOULDER))

ROUND = C.Round(
    DISPLAY_NAME, BODY,
    C.Look(
        HELMET_3D,
        # The breastplate with its ridge and the lame at its foot, rivets in
        # two rows, his belt and buckle, the tunic under the plate.
        C.auto_trunk(X, [W.Band(-5.0, 30.0, UNIFORM), W.Across(-180.0, 180.0, 12.4, UNIFORM_DARK, width=0.6), W.Band(-9.0, -4.6, BELT),
                         W.Dot(0.0, -6.8, 1.6, IRON_LIGHT, OUTLINE), W.Down(0.0, TOP + 3.0, -10.0, IRON_LIGHT, width=0.5),
                         W.Across(-180.0, 180.0, -14.0, IRON_DEEP, width=0.5)]
                     + [W.Dot(u, v, 0.75, RIVET, OUTLINE) for u in (-45.0, -15.0, 15.0, 45.0) for v in (TOP + 4.0, -11.0)]),
        back_pieces=[
            # The iron collar round his neck.
            W.Worn("gorget", [O.Ring(TOP - 2.0, 0.0, 0.2, 7.0, 6.4), O.Ring(TOP + 1.0, 0.0, 0.2, 8.4, 7.6), O.Ring(TOP + 3.0, 0.0, 0.2, 8.0, 7.2)],
                   W.Garment(IRON, IRON_DEEP, [W.Across(-180.0, 180.0, TOP + 0.6, IRON_DEEP, width=0.5), W.Shade()]), lead=2.0),
            # The plate over his near shoulder and the regime's band on that
            # arm, along the arm; his knee plate.
            W.Prop("pauldron", tuple(_SHOULDER + (0.0, -1.6, 0.0)), _BAND, lambda n: _pauldron(), lead=6.0),
            W.Prop("armband", _BAND, tuple(_ELBOW), lambda n: F.band(K, 11.0, 6.4), lead=5.0),
            W.Pinned("armband_emblem", tuple(np.asarray(_BAND) + (0.0, 0.0, 0.0)), lambda: F.emblem(K, 2.8), lead=6.0),
            W.Pinned("knee_plate", tuple(np.asarray(_KNEE) + (0.0, 0.0, 1.0)), _knee, lead=4.0),
        ]),
    STANCE)

if __name__ == "__main__":
    raise SystemExit(main())
