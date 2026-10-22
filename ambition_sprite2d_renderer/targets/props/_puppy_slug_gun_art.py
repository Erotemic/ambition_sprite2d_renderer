"""The puppy-slug gun: a gun that is a puppy slug.

The gun summons puppy slugs, so it is made of one (``characters/puppy_slug``),
in its colours and with its own head:

- the barrel is the wet green body of the slug, with its darker saddle, its
  spots, an eye of the dream in its flank and the pale rippled foot under it;
  its tail curls up at the back;
- the muzzle is the head of the puppy, drawn by the slug's own head, ear and
  stalk pieces, so it is the same animal. Its two eye stalks stand up from
  the head as the sights, and it pants;
- on the top, in a brass collar, a glass jar with a baby slug curled asleep in
  green goo: what it fires;
- under it, a pistol grip of the pale foot of the slug, a brass cap, a brass
  trigger guard and a curl of a trigger.

It is drawn as the held props are: flat, the muzzle pointing RIGHT (+x). The
game draws it on the ground and in the hand (``held_item_art.ron``, row
``puppy_slug_gun``), held at ``GRIP_X`` along it. There is no drop shadow.

This is a ``_``-prefixed helper (no ``render``), so the target registry does
not register it; ``item_icons.write_gauntlet_props`` writes
``gauntlet_puppy_slug_gun.png`` from :func:`picture`.
"""

from __future__ import annotations

import contextlib
import math
from typing import Iterator

from PIL import Image

from ..characters import _person_rig as R
from ..characters import puppy_slug as PS
from ..characters._ai_era_kit import OUTLINE, WHITE, Kit, RGBA, mix, pin

#: The frame its lengths are in, and the picture it is published as (4 pixels
#: to a world pixel at the 36 x 22.5 it is drawn in the game).
FRAME = (96, 60)
OUT = (144, 90)

#: Where the hand holds it, along it (0 at the back): the middle of the grip.
GRIP_X = 25.0 / FRAME[0]

K = Kit(FRAME, out=OUT)

BRASS: RGBA = (214, 168, 84, 255)
BRASS_DARK: RGBA = (140, 100, 44, 255)
BRASS_LIGHT: RGBA = (250, 226, 150, 255)
GLASS: RGBA = (200, 236, 236, 110)
GOO: RGBA = (120, 200, 150, 200)

#: The head of the puppy at the muzzle, in frame pixels.
HEAD = (72.0, 25.0)


@contextlib.contextmanager
def _slug_pieces_in(kit: Kit) -> Iterator[None]:
    """The puppy slug's pieces (``_head``, ``_ear``, ``_stalk_eye``) paint with
    its module kit; while this is open they paint with ``kit``, at this
    picture's scale, so the head is painted and not resized."""
    saved = PS.K
    PS.K = kit
    try:
        yield
    finally:
        PS.K = saved


def _barrel():
    """The body of the slug from its tail to its neck, with the brass bands
    that make it a gun. Painted about ``home`` = the frame's (0, 0)."""

    at = K.at
    top = [(6.0, 25.0), (14.0, 22.0), (28.0, 20.0), (44.0, 18.5), (58.0, 17.5), (66.0, 17.0)]
    low = [(66.0, 37.0), (50.0, 37.0), (30.0, 36.0), (14.0, 35.0), (6.0, 33.0)]

    def shape(d) -> None:
        K.poly(d, [at(*p) for p in top + low], WHITE)
        # The tail at the back curls up: a round end and a tip.
        K.oval(d, at(6.0, 29.0), 4.4, 4.4, WHITE)
        K.poly(d, [at(3.0, 26.0), at(0.6, 19.0), at(4.0, 20.6), at(8.0, 24.0)], WHITE)
        # Brass bands round it.
        for x in (17.0, 59.0):
            K.rrect(d, K.home[0] + x - 2.2, K.home[1] + 16.0 + (59.0 - x) * 0.05, K.home[0] + x + 2.2, K.home[1] + 38.6, 1.0, WHITE)

    def fill(d) -> None:
        d.rectangle([0, 0, K.canvas[0] * 2, K.canvas[1] * 2], fill=PS.SKIN)

    def detail(d) -> None:
        # The saddle along its back.
        K.poly(d, [at(*p) for p in top] + [at(66.0, 24.0), at(44.0, 25.5), at(26.0, 27.0), at(10.0, 28.0)], PS.SADDLE)
        # Its spots: a pale ring, a dark middle, a point of light.
        for x, y, r in ((24.0, 23.5, 1.6), (34.0, 26.0, 1.9), (50.0, 22.0, 1.5), (54.0, 27.5, 1.2), (12.0, 26.0, 1.1)):
            K.oval(d, at(x, y), r * 1.25, r * 1.05, PS.SPOT)
            K.oval(d, at(x, y), r * 0.62, r * 0.55, PS.SKIN_DARK)
            K.oval(d, at(x - r * 0.3, y - r * 0.3), 0.35, 0.35, WHITE)
        # Wet: a line of light down its back, pink at its tail.
        K.line(d, [at(22.0, 21.4), at(36.0, 19.8), at(48.0, 19.0)], PS.SKIN_LIGHT, 0.9)
        K.line(d, [at(4.0, 23.0), at(7.0, 26.4), at(11.0, 27.6)], PS.SHEEN, 1.0)
        # The eye of the dream in its flank, looking at you.
        PS._eye(d, at(42.0, 30.0), 2.6, 2.3, "open", (-0.4, 0.2), (120, 70, 150, 255))
        # The foot under it: a pale band, and its edge ripples.
        edge = [at(6.0 + 60.0 * k / 24.0, 33.4 - 0.8 * math.sin(math.tau * 4.0 * k / 24.0)) for k in range(25)]
        K.poly(d, edge + [at(68.0, 40.0), at(4.0, 40.0)], PS.FOOT)
        K.line(d, edge, PS.FOOT_DARK, 0.6)
        # The brass bands, with a light edge and a rivet.
        for x in (17.0, 59.0):
            y0 = 16.0 + (59.0 - x) * 0.05
            K.rrect(d, K.home[0] + x - 2.2, K.home[1] + y0, K.home[0] + x + 2.2, K.home[1] + 38.6, 1.0, BRASS, OUTLINE, 0.5)
            K.line(d, [at(x - 1.0, y0 + 1.2), at(x - 1.0, 37.4)], BRASS_LIGHT, 0.6)
            K.oval(d, at(x + 0.4, 30.0), 0.7, 0.7, BRASS_DARK)

    return K.solid(("psg_barrel",), shape, fill, detail, outline=1.2, rim=0.34, shade=0.38, shade_colour=PS.SKIN_DARK)


def _grip():
    """The pistol grip of pale slug foot, its brass cap, the trigger guard and
    the trigger."""

    at = K.at

    def shape(d) -> None:
        K.poly(d, [at(19.0, 35.0), at(33.0, 35.0), at(30.0, 54.0), at(16.0, 54.0)], WHITE)
        K.rrect(d, K.home[0] + 14.6, K.home[1] + 52.0, K.home[0] + 31.4, K.home[1] + 57.0, 1.6, WHITE)
        K.stroke(d, [at(33.0, 37.0), at(35.0, 44.0), at(41.0, 45.0), at(44.0, 37.0)], WHITE, 1.6)

    def detail(d) -> None:
        # Ripples across the grip, as the foot of the slug ripples: a grip.
        for k in range(5):
            y = 38.5 + 3.2 * k
            K.line(d, [at(19.0 - 0.15 * (y - 35.0), y), at(25.0, y + 0.8), at(32.6 - 0.16 * (y - 35.0), y)], PS.FOOT_DARK, 0.6)
        K.rrect(d, K.home[0] + 14.6, K.home[1] + 52.0, K.home[0] + 31.4, K.home[1] + 57.0, 1.6, BRASS)
        K.line(d, [at(16.0, 53.2), at(30.0, 53.2)], BRASS_LIGHT, 0.6)
        K.stroke(d, [at(33.0, 37.0), at(35.0, 44.0), at(41.0, 45.0), at(44.0, 37.0)], BRASS, 1.0)

    return K.solid(("psg_grip",), shape, PS.FOOT, detail, outline=1.2, rim=0.3, shade=0.34, shade_colour=PS.FOOT_DARK)


def _trigger():
    """The trigger: a little curl of the slug's tail."""

    def paint(d) -> None:
        K.stroke(d, [K.at(37.0, 37.0), K.at(37.6, 40.4), K.at(39.6, 41.6), K.at(40.8, 40.0)], OUTLINE, 2.0)
        K.stroke(d, [K.at(37.0, 37.0), K.at(37.6, 40.4), K.at(39.6, 41.6), K.at(40.8, 40.0)], PS.EAR, 1.0)

    return K.piece(("psg_trigger",), paint)


def _jar():
    """The glass jar on its back, in a brass collar, and the baby slug asleep
    in the goo in it."""

    at = K.at
    c = (38.0, 10.5)

    def shape(d) -> None:
        K.oval(d, at(*c), 10.0, 7.6, WHITE)
        K.rrect(d, K.home[0] + 27.0, K.home[1] + 15.0, K.home[0] + 49.0, K.home[1] + 20.0, 1.4, WHITE)
        K.rrect(d, K.home[0] + 34.0, K.home[1] + 1.6, K.home[0] + 42.0, K.home[1] + 4.0, 1.0, WHITE)

    def fill(d) -> None:
        d.rectangle([0, 0, K.canvas[0] * 2, K.canvas[1] * 2], fill=mix(GLASS, (255, 255, 255, 255), 0.0))

    def detail(d) -> None:
        # The goo fills the lower half.
        K.poly(d, [at(28.4, 11.0), at(33.0, 10.2), at(38.0, 11.2), at(43.0, 10.0), at(47.6, 11.0), at(46.0, 16.0), at(30.0, 16.0)], GOO)
        # The baby slug, curled asleep: its green body round, its head tucked in.
        K.oval(d, at(39.0, 12.4), 4.6, 3.0, PS.SKIN, OUTLINE, 0.5)
        K.oval(d, at(39.6, 11.6), 2.2, 1.2, PS.SADDLE)
        K.oval(d, at(35.0, 11.4), 2.6, 2.4, PS.FUR, OUTLINE, 0.5)
        K.oval(d, at(33.4, 12.4), 1.2, 1.6, PS.EAR)
        K.line(d, [at(34.4, 10.8), at(35.2, 11.4), at(36.0, 10.8)], PS.INK, 0.4)
        # A bubble, and the light on the glass.
        K.oval(d, at(44.0, 8.0), 0.9, 0.9, (255, 255, 255, 170))
        K.line(d, [at(31.0, 9.0), at(32.4, 6.0), at(35.0, 4.4)], (255, 255, 255, 220), 0.9)
        # The brass collar and the brass lid.
        K.rrect(d, K.home[0] + 27.0, K.home[1] + 15.0, K.home[0] + 49.0, K.home[1] + 20.0, 1.4, BRASS, OUTLINE, 0.5)
        K.line(d, [at(28.4, 16.2), at(47.6, 16.2)], BRASS_LIGHT, 0.6)
        K.rrect(d, K.home[0] + 34.0, K.home[1] + 1.6, K.home[0] + 42.0, K.home[1] + 4.0, 1.0, BRASS, OUTLINE, 0.5)

    return K.solid(("psg_jar",), shape, fill, detail, outline=1.1, rim=0.5, shade=0.2, shade_colour=(120, 170, 180, 255))


def _stalk(k: int, chain) -> object:
    """An eye stalk through ``chain`` (points from where it is placed), as the
    slug's are (``_person_rig.ribbon``). A ``piece``: ``ribbon`` cuts on whole
    frame pixels, which places it wrong in a kit published larger than its
    frame, and this picture is never turned."""
    colour = PS.SKIN if k else PS.SKIN_DARK

    def paint(d) -> None:
        pts = [K.at(x, y) for x, y in chain]
        for edge in (True, False):
            for j in range(len(pts) - 1):
                w = 2.3 * (1.0 - 0.2 * j / max(1, len(pts) - 2))
                K.stroke(d, pts[j:j + 2], OUTLINE if edge else colour, w + (2.4 if edge else 0.0))

    return K.piece(("psg_stalk", k, tuple(chain)), paint)


def picture() -> Image.Image:
    """The gun, ``OUT`` pixels, the muzzle to the right."""
    img = K.new_frame()
    origin = (0.0, 0.0)
    with _slug_pieces_in(K):
        K.place(img, PS._ear(False), (HEAD[0] + 4.6, HEAD[1] - 8.6), "far_ear", -8.0)
        K.place(img, _grip(), origin, "grip")
        K.place(img, _barrel(), origin, "barrel")
        K.place(img, _jar(), origin, "jar")
        K.place(img, _trigger(), origin, "trigger")
        # The eye stalks are its sights: they stand up from the head.
        stalks = []
        for k, root in enumerate(((4.0, -10.0), (-2.4, -10.4))):
            base = (HEAD[0] + root[0], HEAD[1] + root[1])
            at = pin(base)
            chain = R.chain((base[0] - at[0], base[1] - at[1]), 3, 2.6, -84.0 - 8.0 * k, wave=0.0, curl=2.0)
            stalks.append((at, chain))
            K.place(img, _stalk(k, chain), at, f"stalk_{k}")
        K.place(img, PS._head("open"), HEAD, "head")
        for k, (at, chain) in enumerate(stalks):
            K.place(img, PS._stalk_eye("open"), (at[0] + chain[-1][0], at[1] + chain[-1][1]), f"stalk_eye_{k}")
        K.place(img, PS._tongue(0.8), (HEAD[0] + 11.0, HEAD[1] + 8.0), "tongue")
        K.place(img, PS._ear(True), (HEAD[0] - 5.6, HEAD[1] - 6.6), "near_ear", 4.0)
    return K.downsample(img)
