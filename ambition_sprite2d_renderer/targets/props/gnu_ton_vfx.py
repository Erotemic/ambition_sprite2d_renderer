"""The effects of GNU-ton the fighter: the giant's fist comes out of a portal.

On a platform-fighter stage the scholar has no giant under him. For his
smash attacks he opens a portal's line, and the fist of his giant comes out
of it and goes back. The fist is the fist of the boss fight
(``gnu_ton_boss.giant_art.fist``), so the two games show one giant.

The sheet has the fore arm and the fist, cut where the line is. It does NOT
have the line: the game draws each portal (its portal presentation), and no
sprite has a portal in it. The game puts the line where the arm is cut
(``bosses/gnu_ton/fist_lines.rs`` reads ``BEHIND``, ``VIEW`` and
``LINE_HALF``).

A row is drawn for a fighter that looks to the right. The game mirrors it
for a fighter that looks to the left.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image

from ..characters.gnu_ton_boss import _svg as svg
from ..characters.gnu_ton_boss import giant_art as art
from ._character_vfx_common import Canvas, make_spec, publish_canonical, publish_catalog, sheet_files

TARGET_NAME = "gnu_ton_vfx"
# An effect sheet (`SheetRecord::fx`): its sounds are `vfx.gnu_ton.<row>`; it is
# decoded when a character whose moveset names one of its rows is realized; its frames draw their own start and end (they end on a clear frame), so the game draws each at full strength.
FX = {"cue_family": "gnu_ton", "residency": "OwnedByCharacter", "fade": "InItsFrames"}
SHEET_FILES = sheet_files(TARGET_NAME)
FRAME_SIZE = (256, 256)

#: The rows: a name, its frames, the time of a frame in ms. The fist is
#: fully out at `OUT_AT` of the row.
#: Seven frames: with whole frames of 256 a row is 1892 px, under the 2048 of
#: the downlevel WebGL2 limit (`scripts/tests/test_sprite_page_dimensions.py`).
ROWS = [
    ("gnu_fist_forward", 7, 66),
    ("gnu_fist_up", 7, 66),
    ("gnu_fist_down", 7, 66),
]

#: Design units (the giant's) in the frame, across.
VIEW = 328.0
#: The line of the portal is at 0 along the punch; this much of the frame is
#: behind it.
BEHIND = 46.0
#: How far along the punch the middle of the fist is when it is fully out,
#: and when it is all behind the line.
FIST_OUT = 165.0
FIST_IN = -112.0
#: The half length of the portal's line that the game draws.
LINE_HALF = 128.0

#: Parts of a row, as a fraction of it: the game's line is open, the fist is
#: out, the fist starts to go back, the fist is gone.
OPEN_AT, OUT_AT, BACK_AT, GONE_AT = 0.14, 0.34, 0.6, 0.86

SPEED = "#f0e2be"


def _ease_out(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return 1.0 - (1.0 - t) ** 3


def _ease_in(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return t * t


def extension(p: float) -> float:
    """How far out the fist is at `p` of the row: 0 is behind the line, 1 is
    fully out. It goes a little past 1 and comes back (the blow lands)."""
    if p < OPEN_AT:
        return 0.0
    if p < OUT_AT:
        return 1.07 * _ease_out((p - OPEN_AT) / (OUT_AT - OPEN_AT))
    if p < OUT_AT + 0.08:
        return 1.07 - 0.07 * (p - OUT_AT) / 0.08
    if p < BACK_AT:
        return 1.0
    return 1.0 - _ease_in((p - BACK_AT) / (GONE_AT - BACK_AT))


def _fist(ext: float, p: float) -> list[str]:
    """The fore arm and the fist, cut at the line."""
    if ext <= 0.0:
        return []
    x = FIST_IN + (FIST_OUT - FIST_IN) * ext
    # The blow lands: a small shake while it is held out.
    y = 2.5 * math.sin(p * 60.0) if OUT_AT <= p < BACK_AT else 0.0
    wrist = x - 92.0
    body = art.outlined(svg.capsule((wrist - 420.0, y), (wrist, y), 40.0, 44.0), art.C["fur"],
                        [art.path(svg.capsule((wrist - 420.0, y + 18.0), (wrist, y + 18.0), 16.0, 20.0), art.C["dark"])],
                        "clip-fore-arm")
    body += art.grp(art.fist("fist"), f"translate({x:.1f} {y:.1f}) scale(-1 1)")
    out = [art._cut("cut-line", ("x", 0.0, False)), '<g clip-path="url(#cut-line)">'] + body + ["</g>"]
    # Lines of speed behind the knuckles while the fist goes out.
    if OPEN_AT < p < OUT_AT + 0.04:
        fast = 1.0 - abs((p - OPEN_AT) / (OUT_AT - OPEN_AT) - 0.5)
        for i, dy in enumerate((-58.0, -20.0, 24.0, 60.0)):
            tail = max(8.0, x - 150.0 - 30.0 * (i % 2))
            head = max(tail + 6.0, x - 96.0)
            out.append(art.line([(tail, dy), (head, dy)], SPEED, 3.0 + 2.0 * fast))
    return out


#: For each row: how the drawing (a punch to the right from a line at 0) is
#: turned, and the corner of the view.
_TURNS = {
    "gnu_fist_forward": (0.0, (-BEHIND, -VIEW / 2.0)),
    # Up out of a line on the floor.
    "gnu_fist_up": (-90.0, (-VIEW / 2.0, BEHIND - VIEW)),
    # Down out of a line over the head.
    "gnu_fist_down": (90.0, (-VIEW / 2.0, -BEHIND)),
}


def render_row(anim: str, p: float) -> Image.Image:
    turn, (x0, y0) = _TURNS[anim]
    svg.configure(dx=0.0, dy=0.0, ink=art.INK, ow=art.OW, colors=art.C)
    body = _fist(extension(p), p)
    svg.part("punch", "Punch", "punch", "fist", 10, art.grp(body, f"rotate({turn:g})"))
    return art._raster(art._document((x0, y0, VIEW, VIEW)), FRAME_SIZE)


def _drawer(anim: str):
    def draw(canvas: Canvas, p: float) -> None:
        canvas.image.alpha_composite(render_row(anim, p).resize(canvas.image.size, Image.LANCZOS))

    return draw


DRAWERS = {name: _drawer(name) for name, _, _ in ROWS}

SPECS = {
    "gnu_fist_forward": make_spec("summoned_limb", "The giant's fist comes out of a portal's line in front of the scholar and goes back.",
                                  placement="caster_front", orientation="facing", mirror_x=True, rotate_safe=False, size=240),
    "gnu_fist_up": make_spec("summoned_limb", "The giant's fist comes up out of a portal's line on the floor in front of the scholar.",
                             placement="caster_front", orientation="facing", mirror_x=True, rotate_safe=False, size=240),
    "gnu_fist_down": make_spec("summoned_limb", "The giant's fist comes down out of a portal's line over the scholar's reach.",
                               placement="caster_front", orientation="facing", mirror_x=True, rotate_safe=False, size=240),
}

ORIGINS = {name: (FRAME_SIZE[0] * 0.5, FRAME_SIZE[1] * 0.5) for name, _, _ in ROWS}


def render(out_dir: str | Path, **opts):
    del opts
    return publish_catalog(
        fx=FX,
        target_name=TARGET_NAME,
        display_name="GNU-ton Detached VFX",
        character_context_id="npc_gnu_ton",
        character_context_display="GNU-ton",
        rows=ROWS,
        drawers=DRAWERS,
        specs=SPECS,
        origins=ORIGINS,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        supersample=1,
        # A line, then a fist: the frames differ in shape, and the game does
        # not draw a trimmed frame of an effect in its own shape.
        whole_frames=True,
    )


def render_canonical(out_dir: str | Path, **opts):
    del opts
    return publish_canonical(
        target_name=TARGET_NAME,
        rows=ROWS,
        drawers=DRAWERS,
        specs=SPECS,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        supersample=1,
    )
