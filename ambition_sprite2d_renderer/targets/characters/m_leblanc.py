"""Sprite generator for Madam LeBlanc: the number theorist who signed a man's
name, and let the theorem argue.

A parody of Sophie Germain, through the pseudonym "M. LeBlanc" that she wrote
under when the schools would not have a woman.

The look (2026-10-13): a woman of about thirty seen three quarters from the
front, facing right, in the dress of her years (about 1800). Dark hair put up
high at the back of her head, with a green ribbon through it and curls at her
temples; a calm round face with a strong brow. A white gown with its waist
high under the bust and short full sleeves, a green sash, a green shawl down
her back. She stands straight and she is not in a hurry.

She is drawn as a woman of her time and as herself, not as one shape that
every woman of the cast shares (Jon, 2026-10-13: "The women need to read more
as women, and there needs to be variation"). She is a grown woman, not a
mascot. She holds nothing; there is no drop shadow.

What she shows: the letter she sent anyway, a prime that comes with its own
witness (11, and 23 after it), and the figure that sand makes on a plate that
sings.

She is a person of ``_person_rig``: the bones, the poses and the frame are
shared; the head, the gown, how she stands and what she shows are hers.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import List

from ._ai_era_kit import OUTLINE, WHITE, RGBA, mix, pin
from . import _person_rig as R
from ._person_rig import Build, Person, Stamp, loop, shot

TARGET_NAME = "m_leblanc"

ACTOR_METADATA = {
    "actor": {
        "character_id": TARGET_NAME,
        "display_name": "Madam LeBlanc",
    },
    "body": {
        "body_plan": "Scholar",
        "body_kind": "Grounded",
        "traits": [
            "mathematician",
            "peaceful",
            "expressive",
            "three_quarter_rig",
        ],
    },
    "visual": {
        "default_pose": "idle",
        "facing_policy": "three_quarter",
    },
    "provenance": {
        "variant_family": TARGET_NAME,
        "variant_id": "opus_4_8_render_wiring_2026_07_17",
        "lineage": [
            {
                "revision_id": "gpt_5_6_leblanc_rig_2026_07_17",
                "creator_kind": "model",
                "creator": "gpt-5.6-thinking",
                "contribution": "three_quarter_svg_rig_and_clip_authoring_for_sophie_germain",
                "date": "2026-07-17",
            },
            {
                "revision_id": "opus_4_8_render_wiring_2026_07_17",
                "creator_kind": "model",
                "creator": "claude-opus-4.8",
                "contribution": "module_render_entry_point_rows_and_actor_metadata_so_the_rig_registers_and_installs",
                "parent_revision_id": "gpt_5_6_leblanc_rig_2026_07_17",
                "date": "2026-07-17",
            },
        ],
    },
    "tags": ["npc", "mathematician", "peaceful", "custom"],
}


ACTOR_METADATA.update(
    {
        "authoring_description": (
            "Madam LeBlanc is a parody of Sophie Germain through the male pseudonym 'M. LeBlanc' that "
            "she used to correspond and submit work when institutions excluded women. The character "
            "keeps the false name as a title of defiance and foregrounds number theory, elasticity, "
            "and locked academic doors."
        ),
        "gameplay_description": (
            "Use as a number theorist, disguised scholar, resilient quest giver, or precision "
            "playable character. Her mechanics should reward proofs that arrive with witnesses, false "
            "keys that open unjust gates, and attacks based on Sophie Germain primes or vibrating "
            "plates."
        ),
    }
)
ACTOR_METADATA.setdefault("dialogue_hints", {}).setdefault(
    "barks",
    [
        'I sent the proof anyway, signed Madam LeBlanc, and let the theorem argue.',
        'A locked door deserves a false key.',
        'I admire a number that arrives with its own witness.',
    ],
)



GOWN: RGBA = (246, 242, 230, 255)
GOWN_DARK: RGBA = (196, 190, 184, 255)
GOWN_LIGHT: RGBA = (255, 253, 246, 255)
GREEN: RGBA = (70, 140, 96, 255)
GREEN_DARK: RGBA = (42, 92, 70, 255)
GREEN_LIGHT: RGBA = (118, 186, 134, 255)
SKIN: RGBA = (238, 206, 182, 255)
SKIN_SHADE: RGBA = (208, 168, 148, 255)
SKIN_DEEP: RGBA = (162, 112, 100, 255)
HAIR: RGBA = (72, 48, 40, 255)
HAIR_LIGHT: RGBA = (126, 90, 70, 255)
SLIPPER: RGBA = (70, 140, 96, 255)
INK: RGBA = (28, 24, 32, 255)
PAPER: RGBA = (250, 244, 228, 255)
PAPER_DARK: RGBA = (198, 186, 160, 255)
SEAL: RGBA = (196, 60, 58, 255)
CHALK: RGBA = (252, 236, 170, 255)
CHALK_DARK: RGBA = (200, 140, 60, 255)
SAND: RGBA = (236, 206, 140, 255)
PLATE: RGBA = (92, 100, 124, 255)

#: 160 cm, and straight: narrow shoulders, her neck long, her head high.
BUILD = Build(hip_up=45.0, thigh=22.0, shin=20.3, neck=(0.2, -35.0), upper=18.0, fore=17.0, near_shoulder=(-4.4, -30.6), far_shoulder=(5.4, -30.2),
              near_hip=(-3.8, 0.0), far_hip=(3.8, 0.0), head_up=(0.8, -12.6), height=103.0, half_width=(12.0, 13.0))

L = Person(TARGET_NAME, BUILD)
K = L.K
P = L.P
TOP = BUILD.neck[1] - 2.0


# ---- The pieces --------------------------------------------------------------


def _front(d, hb: float, hf: float) -> None:
    """The green sash under her bust, the low square neck of the gown, and the
    long folds of its skirt."""
    K.poly(d, [K.at(-9.0, TOP + 16.0), K.at(10.0, TOP + 17.0), K.at(10.0, TOP + 19.6), K.at(-9.0, TOP + 18.6)], GREEN)
    K.poly(d, [K.at(-4.6, TOP + 18.4), K.at(-1.6, TOP + 18.6), K.at(-3.4 - hb * 0.3, TOP + 34.0), K.at(-6.0 - hb * 0.3, TOP + 33.0)], GREEN)
    K.poly(d, [K.at(0.4, TOP - 1.0), K.at(7.6, TOP - 1.0), K.at(7.0, TOP + 6.4), K.at(1.2, TOP + 6.4)], SKIN_SHADE)
    K.line(d, [K.at(1.0, TOP + 6.6), K.at(7.2, TOP + 6.6)], GOWN_DARK, 0.7)
    for x in (-6.0, -1.4, 3.6, 7.6):
        K.line(d, [K.at(x * 0.7, TOP + 21.0), K.at(x * 1.5 - hb * 0.4 + hf * 0.2, 40.0)], GOWN_DARK, 0.6)
    K.poly(d, [K.at(-20.0 - hb, BUILD.hip_up - 9.0), K.at(20.0 + hf, BUILD.hip_up - 9.0), K.at(20.0 + hf, BUILD.hip_up - 7.4), K.at(-20.0 - hb, BUILD.hip_up - 7.4)],
           GREEN_LIGHT)


L.torso = R.make_figure(K, ("leblanc",), GOWN, GOWN_DARK, back=(6.8, 7.2, 6.4, 8.0, 12.4), front=(6.0, 8.8, 7.0, 8.6, 12.0), hem_y=BUILD.hip_up - 5.0, top=TOP,
                        shoulders=((-4.4, -30.0), (5.0, -29.6)), shoulder_r=(4.6, 4.2), waist_y=TOP + 18.0, shade_from=7.4, detail=_front)


def _shawl(ctx) -> List[Stamp]:
    """Her shawl: over her shoulders and down her back to her knees."""
    sway = int(round(float(ctx.pose["hem"][0]) * 1.4))

    def shape(d) -> None:
        K.poly(d, [K.at(-3.6, TOP + 1.0), K.at(-8.6, TOP + 5.0), K.at(-9.6, -14.0), K.at(-11.6 - sway, 14.0), K.at(-8.0 - sway, 20.0), K.at(-4.0, 16.0),
                   K.at(2.0, TOP + 8.0), K.at(3.0, TOP + 2.0)], WHITE)

    def detail(d) -> None:
        K.line(d, [K.at(-6.6, TOP + 8.0), K.at(-9.0 - sway * 0.6, 14.0)], GREEN_DARK, 0.7)
        for y in (15.0, 17.6):
            K.line(d, [K.at(-11.0 - sway, y - 2.0), K.at(-5.0, y)], GREEN_LIGHT, 0.6)

    return [(K.solid(("shawl", sway), shape, GREEN, detail, outline=1.3, rim=0.25, shade=0.4, shade_colour=GREEN_DARK), ctx.hip, "shawl", ctx.lean)]


L.layers["back"].append(_shawl)


def _hair_shape(d) -> None:
    # Put up high at the back of her head, and curls at her temple.
    K.oval(d, K.at(-1.0, -4.6), 9.0, 8.6, WHITE)
    K.oval(d, K.at(-6.6, -10.4), 5.0, 4.6, WHITE)
    for x, y in ((-3.6, 2.0), (-4.4, 5.4)):
        K.oval(d, K.at(x, y), 2.2, 2.2, WHITE)


def _hair(d) -> None:
    K.poly(d, [K.at(20.0, -8.8), K.at(8.4, -8.8), K.at(5.0, -7.4), K.at(1.6, -5.4), K.at(-1.0, -3.6), K.at(-2.4, -0.6), K.at(-2.2, 3.0), K.at(-3.0, 7.6),
               K.at(-20.0, 7.6), K.at(-20.0, -26.0), K.at(20.0, -26.0)], HAIR)
    for strand in ([(6.6, -9.8), (0.0, -9.0), (-5.0, -6.0)], [(-3.6, -12.0), (-7.0, -13.4), (-10.0, -10.6)], [(-4.0, -8.6), (-8.4, -8.4)]):
        K.line(d, [K.at(x, y) for x, y in strand], HAIR_LIGHT, 0.6)
    for x, y in ((-3.6, 2.0), (-4.4, 5.4)):
        K.oval(d, K.at(x, y), 1.3, 1.3, None, HAIR_LIGHT, 0.5)  # type: ignore[arg-type]
    # The green ribbon through it.
    K.line(d, [K.at(4.6, -10.6), K.at(-1.0, -9.6), K.at(-5.0, -6.4)], GREEN, 1.3)
    K.poly(d, [K.at(-5.0, -6.4), K.at(-8.4, -4.4), K.at(-6.6, -3.0)], GREEN)


_head = R.make_head(K, ("leblanc",), SKIN, SKIN_SHADE, SKIN_DEEP, skull=(0.0, -2.2, 7.8, 8.6), jaw=(2.2, 3.6, 5.8, 6.8),
                    nose=((7.2, 0.8), (8.6, 3.0), (8.2, 3.8), (7.2, 4.0)), ear=None, shape=_hair_shape, under=_hair)
_eyes = R.make_eyes(K, (2.0, -0.4), (7.4, -0.6), ink=INK, iris=(84, 60, 44, 255), size=0.9, lash=0.5)
_brows = R.make_brows(K, [(-0.4, -4.0), (2.0, -4.8), (4.6, -4.2)], [(6.0, -4.4), (7.4, -4.8), (8.8, -4.2)], HAIR, 1.0)
_mouth = R.make_mouth(K, (5.6, 7.2), (130, 56, 66, 255), wide=0.8, lips=(196, 104, 110, 255))

L.head_layers = lambda pose: [(_head(), "head"), (_eyes(str(pose["eyes"])), "eyes"), (_brows(R.brow_mood(pose)), "brows"),
                              (_mouth(str(pose["mouth"])), "mouth")]
L.neck = R.make_neck(K, SKIN_SHADE, 3.8)
# A short full sleeve to above her elbow, and her arm bare under it.
L.upper_arm = lambda near: [(0.55, 1.0, 4.8, 4.4, SKIN if near else SKIN_SHADE), (0.0, 0.6, 7.4, 6.6, GOWN if near else GOWN_DARK)]
L.forearm = lambda near: [(0.0, 1.0, 4.4, 3.8, SKIN if near else SKIN_SHADE)]
L.thigh = lambda near: [(0.0, 1.0, 6.4, 5.4, GOWN if near else GOWN_DARK)]
L.shin = lambda near: [(0.0, 1.0, 5.4, 4.4, GOWN if near else GOWN_DARK)]
L.hand = R.make_hand(K, SKIN, SKIN_SHADE, SKIN_DEEP, size=0.85)
L.shoe = R.make_shoe(K, SLIPPER, GREEN_DARK, BUILD.ankle_up, long=0.9)


# ---- How she holds herself ---------------------------------------------------

#: Her hands one over the other at her sash.
HELD_NEAR = (6.0, 12.5)
HELD_FAR = (-1.0, 21.0)
L.set_rest(na=HELD_NEAR, fa=HELD_FAR, nh="flat", nf=(-3.4, 0.0, 0.0), ff=(4.4, 0.0, 0.0))


@L.row
def idle(i: int, n: int):
    # Straight and quiet; now and then she looks at the door that is shut.
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.3 + 0.3 * s), head=(0.2, -0.2 * s, -2.0 + 3.0 * c), eyes="closed" if i == n - 2 else "open", brows=-1.0 if c < -0.6 else 0.0)


@L.row
def walk(i: int, n: int):
    # Small steps under a long skirt, and her hands stay where they are.
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 6.2, 3.0)
    return P(hip=(0.5, 0.7 * math.cos(2.0 * ph)), lean=1.0, head=(0.0, 0.0, 1.0 * s), nf=nf, ff=ff, hem=(1.0 + 1.5 * abs(c), 0.5 + 1.5 * abs(c)))


@L.row
def talk(i: int, n: int):
    # She makes her case with one open hand. She has made it before.
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.3 * s), head=(0.3, 0.0, 2.0 * s), na=(13.0 + 2.0 * c, 4.0 - 3.0 * max(0.0, s)), nh="open", mouth=("open", "smile", "o", "smile")[i % 4],
             brows=1.0 if s > 0.4 else 0.0)


@L.row
def interact(i: int, n: int):
    # She gives the letter over. It is signed with the other name.
    out = P(hip=(1.0, 1.0), lean=5.0, na=(23.0, 2.0), nh="soft", brows=1.0)
    return L.keys(shot(i, n), [(0.0, P()), (0.3, out), (0.8, dict(out, na=(23.0, 3.0))), (1.0, P())])


L.rows = [("idle", 8, 150), ("walk", 8, 120), ("talk", 8, 120), ("interact", 8, 130)]


# ---- From the front ------------------------------------------------------------

FRONT_HEM = BUILD.hip_up - 5.0


def _front_gown(d) -> None:
    """Her gown from the front: the low square neck, the green sash under her
    bust and its ends, the shawl on each shoulder, the folds."""
    by = TOP + 12.5
    K.poly(d, [K.at(-4.4, TOP - 1.0), K.at(4.4, TOP - 1.0), K.at(4.0, TOP + 6.0), K.at(-4.0, TOP + 6.0)], SKIN)
    K.line(d, [K.at(-4.0, TOP + 6.0), K.at(4.0, TOP + 6.0)], GOWN_DARK, 0.6)
    for sx in (-1.0, 1.0):
        K.oval(d, K.at(4.0 * sx, by + 0.6), 2.4, 1.8, GOWN_LIGHT)
        K.poly(d, [K.at(4.6 * sx, TOP - 1.0), K.at(9.0 * sx, TOP + 2.0), K.at(9.6 * sx, -12.0), K.at(7.4 * sx, -10.0), K.at(6.6 * sx, TOP + 5.0)], GREEN)
        K.line(d, [K.at(6.6 * sx, TOP + 5.0), K.at(7.4 * sx, -10.0)], GREEN_DARK, 0.6)
    K.poly(d, [K.at(-8.6, by + 4.0), K.at(8.6, by + 4.0), K.at(8.6, by + 7.0), K.at(-8.6, by + 7.0)], GREEN)
    K.poly(d, [K.at(1.6, by + 7.0), K.at(4.0, by + 7.0), K.at(5.4, by + 22.0), K.at(2.8, by + 22.0)], GREEN)
    K.line(d, [K.at(-8.6, by + 7.0), K.at(8.6, by + 7.0)], GREEN_DARK, 0.6)
    for x in (-5.0, -1.6, 1.6, 5.0):
        K.line(d, [K.at(x, by + 9.0), K.at(x * 1.7, FRONT_HEM - 2.0)], GOWN_DARK, 0.6)


def _front_hair_shape(d) -> None:
    # Up on top of her head in a knot, and a curl at each temple.
    K.oval(d, K.at(0.0, -5.6), 9.0, 7.2, WHITE)
    K.oval(d, K.at(0.0, -13.0), 4.4, 3.8, WHITE)
    for sx in (-1.0, 1.0):
        K.oval(d, K.at(7.8 * sx, 0.6), 2.4, 3.4, WHITE)


def _front_hair(d) -> None:
    K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, 5.0), K.at(6.4, 5.0), K.at(6.8, -2.6), K.at(4.4, -6.6), K.at(0.0, -7.8), K.at(-4.4, -6.6),
               K.at(-6.8, -2.6), K.at(-6.4, 5.0), K.at(-20.0, 5.0)], HAIR)
    K.line(d, [K.at(0.0, -11.6), K.at(0.0, -7.8)], (48, 30, 28, 255), 0.5)
    K.oval(d, K.at(0.0, -13.0), 2.8, 2.2, None, HAIR_LIGHT, 0.6)  # type: ignore[arg-type]
    for sx in (-1.0, 1.0):
        K.line(d, [K.at(2.0 * sx, -10.6), K.at(5.6 * sx, -7.6)], HAIR_LIGHT, 0.6)
        K.oval(d, K.at(7.8 * sx, 0.8), 1.4, 2.2, None, HAIR_LIGHT, 0.6)  # type: ignore[arg-type]


def _front_nose(d) -> None:
    K.line(d, [K.at(-0.2, 0.6), K.at(-0.9, 3.2), K.at(0.0, 3.9), K.at(0.9, 3.2)], SKIN_DEEP, 0.5)


L.front_torso = R.make_front_torso(K, ("leblanc",), GOWN, GOWN_DARK, [(TOP, 3.4), (TOP + 3.6, 7.0), (TOP + 12.5, 8.6), (-13.0, 7.0), (0.0, 8.6), (FRONT_HEM, 12.4)],
                                   shoulder=(5.8, -30.4, 3.8, 4.2), detail=_front_gown)
L.front_head_layers = R.front_face(R.make_front_head(K, ("leblanc",), SKIN, SKIN_DEEP, wide=7.4, jaw=6.0, chin=3.6, shape=_front_hair_shape, hair=_front_hair,
                                                    face=_front_nose),
                                   R.make_front_eyes(K, ("leblanc",), ink=INK, iris=(84, 60, 44, 255), spread=3.2, y=-0.4, size=0.85, lash=0.5),
                                   R.make_front_brows(K, ("leblanc",), HAIR, spread=3.2, y=-3.8, width=0.9),
                                   R.make_front_mouth(K, ("leblanc",), y=7.8, colour=(130, 56, 66, 255), lips=(196, 104, 110, 255), wide=0.75))
L.front_shoe = R.make_front_shoe(K, SLIPPER, GREEN_DARK, BUILD.ankle_up, wide=0.85)
L.front_span = (6.8, 4.2)
R.add_front_rows(L)

# ---- What she shows ----------------------------------------------------------


def _letter():
    def shape(d) -> None:
        K.rrect(d, K.home[0] - 6.4, K.home[1] - 4.2, K.home[0] + 6.4, K.home[1] + 4.2, 0.6, WHITE)

    def detail(d) -> None:
        K.line(d, [K.at(-6.4, -4.2), K.at(0.0, 0.6), K.at(6.4, -4.2)], PAPER_DARK, 0.7)
        K.oval(d, K.at(0.0, 0.8), 1.8, 1.8, SEAL)

    return K.solid(("letter",), shape, PAPER, detail, outline=1.0, rim=0.2, shade=0.35, shade_colour=PAPER_DARK)


def _plate(mode: int):
    """A plate that sings, and the figure the sand makes on it."""

    def shape(d) -> None:
        K.rrect(d, K.home[0] - 7.0, K.home[1] - 7.0, K.home[0] + 7.0, K.home[1] + 7.0, 0.8, WHITE)

    def detail(d) -> None:
        if mode % 2 == 0:
            K.line(d, [K.at(-7.0, -7.0), K.at(7.0, 7.0)], SAND, 0.9)
            K.line(d, [K.at(7.0, -7.0), K.at(-7.0, 7.0)], SAND, 0.9)
            K.oval(d, K.home, 3.4, 3.4, None, SAND, 0.8)  # type: ignore[arg-type]
        else:
            K.line(d, [K.at(0.0, -7.0), K.at(0.0, 7.0)], SAND, 0.9)
            K.line(d, [K.at(-7.0, 0.0), K.at(7.0, 0.0)], SAND, 0.9)
            for sx in (-1.0, 1.0):
                for sy in (-1.0, 1.0):
                    K.oval(d, K.at(3.5 * sx, 3.5 * sy), 1.8, 1.8, None, SAND, 0.7)  # type: ignore[arg-type]

    return K.solid(("plate", mode % 2), shape, PLATE, detail, outline=1.0, rim=0.3, shade=0.4, shade_colour=(52, 56, 80, 255))


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    if ctx.anim == "interact" and 0.2 <= ctx.u <= 0.9:
        out.append((_letter(), (ctx.hand[0] + 7.0, ctx.hand[1] - 2.0), "letter", -8.0))
    elif ctx.anim == "talk":
        # A prime, and the prime it is the witness of.
        which = "11" if ctx.i % 8 < 4 else "23"
        out.append((R.glyph(K, which, 9.0, CHALK, CHALK_DARK), (ctx.head[0] + 22.0, ctx.head[1] - 14.0 - (1.0 if ctx.i % 2 else 0.0)), "prime", 0.0))
    elif ctx.anim == "idle" and ctx.i in (4, 5):
        out.append((_plate(ctx.i), pin((ctx.head[0] + 24.0, ctx.head[1] - 6.0)), "plate", 0.0))
    return out


L.effects = _effects
ROWS = L.rows


def _render_frame(anim: str, frame_idx: int, nframes: int):
    return L.render_frame(anim, frame_idx, nframes)


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    return L.render(out_dir, ACTOR_METADATA)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render the Madam LeBlanc spritesheet.")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[2] / "generated" / TARGET_NAME)
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


if __name__ == "__main__":
    raise SystemExit(main())
