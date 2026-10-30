"""The giant gnu's arms are rigid, and only the forearm and the fist go
through the near line of a blow, square to it (Jon, 2026-10-24: "a lot of the
punches will clip the upper arm through the portal ... I really don't like
the bendy arm").

Each check runs on the POSED PIECES of every frame of every blow row (the
geometry the part flipbook publishes), not on the pose's numbers: a later
edit of a pose, of a piece, or of the way a scene places them cannot put the
upper arm through a portal and pass.
"""
from __future__ import annotations

import math
import re
from pathlib import Path

import pytest

from ambition_sprite2d_renderer.targets.characters.gnu_ton_boss import _pieces as pc
from ambition_sprite2d_renderer.targets.characters.gnu_ton_boss import giant_art as g
from ambition_sprite2d_renderer.targets.characters.gnu_ton_boss import sprite_generator as sg

ARM_BLOWS = [b for b, spec in g.BLOWS.items() if spec["arm"] != "leg"]
PARTS = ("windup", "strike", "hold", "recover")
FRAMES = {name: count for name, count, _ms in sg.ANIMATIONS}
#: The ink of a piece is outside its fill: a margin for it.
INK = 4.0
#: The angle the forearm and the fist may be off square while through.
SQUARE_DEGREES = 1.0
#: The place of the design that the published frame shows.
FRAME_BOX = (-g.CANVAS_ORIGIN[0], -g.CANVAS_ORIGIN[1], g.CANVAS[0] - g.CANVAS_ORIGIN[0], g.CANVAS[1] - g.CANVAS_ORIGIN[1])


def _phases(n):
    """Each frame of a row of ``n`` frames, and the time between frames."""
    return sorted({k / n for k in range(n)} | {(k + 0.5) / n for k in range(n)})


def _capsule(r0, r1, length, steps=12):
    """Points round a capsule from (0, 0) to (0, length), radii r0 to r1."""
    out = []
    for k in range(steps + 1):
        t = k / steps
        r = r0 + (r1 - r0) * t
        out += [(-r, length * t), (r, length * t)]
    for k in range(24):
        a = 2.0 * math.pi * k / 24
        out += [(r0 * math.cos(a), r0 * math.sin(a)), (r1 * math.cos(a), length + r1 * math.sin(a))]
    return out


#: Each piece of an arm in its own place, as points (`giant_art`'s pieces).
UPPER = _capsule(46.0 + INK, 36.0 + INK, g.ARM_UPPER)
FORE = _capsule(38.0 + INK, 44.0 + INK, g.ARM_FORE)
TUFT = [(x * 1.1, y * 1.1) for x, y in [(-30, -14), (30, -14), (26, 22), (10, 50), (0, 26), (-12, 56), (-26, 20)]]


def _posed(anim, phase):
    """The placed pieces of one frame, by track."""
    return {placed.name: placed for placed in g.scene_for(g.pose_for(anim, phase)).items}


def _depth(blow, p):
    """How far ``p`` is past the near line of ``blow`` (less than 0: on the
    giant's side)."""
    (cx, cy), (nx, ny) = g.BLOWS[blow]["line"]
    return -((p[0] - cx) * nx + (p[1] - cy) * ny)


def _points(placed, local):
    return [pc.apply(placed.full(), p) for p in local]


def _rows(blow):
    """Each frame of the blow's rows while its pair is open: from `open_from`
    of the windup to `close_at` of the recover."""
    b = g.BLOWS[blow]
    for part in PARTS:
        anim = f"{blow}_{part}"
        for phase in _phases(FRAMES[anim]) + ([b["close_at"]] if part == "recover" else []):
            if part == "windup" and phase < b["open_from"] or part == "recover" and phase > b["close_at"]:
                continue
            yield anim, phase


def _across(blow, p):
    """How far ``p`` is along the near line of ``blow`` from its middle."""
    (cx, cy), (nx, ny) = g.BLOWS[blow]["line"]
    return (p[0] - cx) * -ny + (p[1] - cy) * nx


#: Half the length of a near line (the game's `half`, 84 world units), and a
#: margin round the opening.
HALF = 84.0 / 0.65
MARGIN = 40.0


@pytest.mark.parametrize("blow", ARM_BLOWS)
def test_the_upper_arm_never_goes_into_the_entrance_portal(blow):
    """Two rules, each frame of the blow's rows (its pair is open from the
    start of its tell to the end of its way back):

    * While the forearm or the fist is through the line (the limb is
      carried, and the portal draws its parts past the PLANE at the far
      line), no part of the upper arm or of the hair at the elbow is past
      the plane of the line, along its whole length.
    * At no time is any of it in the opening (past the line, within the
      line's length and a margin): it never goes through, or seems to. In
      the tell, no part of the arm is.

    The pair opens at `open_from` of the windup and is closed at `close_at`
    of the recover (the game reads the same numbers, `blows::Limb`).
    """
    slot = g.LIMB_SLOTS["arm-left" if g.BLOWS[blow]["arm"] == "left" else "arm-right"]
    worst = []
    carried_frames = 0
    for anim, phase in _rows(blow):
        posed = _posed(anim, phase)
        upper = _points(posed[f"limb:{slot}:upper"], UPPER) + _points(posed[f"limb:{slot}:tuft"], TUFT)
        fist = posed[f"limb:{slot}:fist"].full()
        through = _points(posed[f"limb:{slot}:fore"], FORE) + [pc.apply(fist, (r * math.cos(a), r * math.sin(a)))
                                                                for r in (0.0, 70.0) for a in (0.0, 1.57, 3.14, 4.71)]
        carried = max(_depth(blow, p) for p in through) > 0.0
        carried_frames += carried
        deepest = max(_depth(blow, p) for p in upper)
        if carried and deepest >= 0.0:
            worst.append(f"{anim} at {phase:.3f}: carried, the upper arm {deepest:.1f} past the plane")
        in_opening = [p for p in upper if _depth(blow, p) >= 0.0 and abs(_across(blow, p)) <= HALF + MARGIN]
        if in_opening:
            worst.append(f"{anim} at {phase:.3f}: the upper arm is in the opening")
        # In the tell nothing of the arm is in the opening: it is cocked in
        # front of it.
        if anim.endswith("_windup") and [p for p in through if _depth(blow, p) >= 0.0 and abs(_across(blow, p)) <= HALF + MARGIN]:
            worst.append(f"{anim} at {phase:.3f}: the forearm is in the opening in the tell")
    assert carried_frames > 0, f"{blow}: the limb is never carried"
    assert not worst, "the upper arm goes into the portal:\n" + "\n".join(worst)


#: The outline of a fist (`giant_art.fist`) about its middle: the mitt, the
#: knuckles, the cuff and the tuft on it.
FIST = [(-56, -52), (0, -66), (52, -56), (64, 0), (54, 54), (0, 66), (-52, 54), (-70, 0), (-84, -46), (-94, -27),
        (-84, 52), (-94, 27), (46, -62), (88, -56), (92, 56), (46, 62), (-20, -80), (18, -84), (38, -64)]


@pytest.mark.parametrize("blow", ARM_BLOWS)
def test_what_goes_through_the_line_goes_through_its_opening(blow):
    """While the limb is carried (the strike, the hold, the recover), every
    part of the forearm and the fist past the plane of the near line is in
    the line's opening, by the width of the ink: the portal draws what is
    past the plane at the far line, cut at ITS ends, so a fist past the end
    of the near line comes out of the far one cut square (Jon, 2026-10-30,
    the left hook)."""
    slot = g.LIMB_SLOTS["arm-left" if g.BLOWS[blow]["arm"] == "left" else "arm-right"]
    worst = []
    for anim, phase in _rows(blow):
        if anim.endswith("_windup"):
            continue
        posed = _posed(anim, phase)
        past = [p for piece, local in (("fore", FORE), ("fist", FIST))
                for p in _points(posed[f"limb:{slot}:{piece}"], local) if _depth(blow, p) > 0.0]
        out = max((abs(_across(blow, p)) for p in past), default=0.0)
        if out > HALF - INK:
            worst.append(f"{anim} at {phase:.3f}: {out:.1f} from the middle of the line")
    assert not worst, f"{blow}: the limb goes past the end of its line (half {HALF:.1f}):\n" + "\n".join(worst)


@pytest.mark.parametrize("blow", ARM_BLOWS)
def test_the_forearm_and_the_fist_go_through_square(blow):
    slot = g.LIMB_SLOTS["arm-left" if g.BLOWS[blow]["arm"] == "left" else "arm-right"]
    (_c, (nx, ny)) = g.BLOWS[blow]["line"]
    way = (-nx, -ny)
    through = 0
    for anim, phase in _rows(blow):
        posed = _posed(anim, phase)
        fore = posed[f"limb:{slot}:fore"]
        fist = posed[f"limb:{slot}:fist"]
        elbow, wrist = pc.apply(fore.full(), (0.0, 0.0)), pc.apply(fore.full(), (0.0, g.ARM_FORE))
        middle = pc.apply(fist.full(), (0.0, 0.0))
        def in_opening(points):
            return any(_depth(blow, p) > 0.0 and abs(_across(blow, p)) <= HALF + MARGIN for p in points)

        if in_opening(_points(fore, FORE)):
            through += 1
            d = math.hypot(wrist[0] - elbow[0], wrist[1] - elbow[1])
            cos = ((wrist[0] - elbow[0]) * way[0] + (wrist[1] - elbow[1]) * way[1]) / d
            assert cos >= math.cos(math.radians(SQUARE_DEGREES)), f"{anim} at {phase:.3f}: the forearm is not square"
        # The fist (its knuckles are 70 past its middle) is in the opening.
        if in_opening([(middle[0] + way[0] * r, middle[1] + way[1] * r) for r in (-70.0, 0.0, 70.0)]):
            d = math.hypot(middle[0] - wrist[0], middle[1] - wrist[1])
            cos = ((middle[0] - wrist[0]) * way[0] + (middle[1] - wrist[1]) * way[1]) / d
            assert cos >= math.cos(math.radians(SQUARE_DEGREES)), f"{anim} at {phase:.3f}: the fist is not square"
    assert through > 0, f"{blow}: the forearm never goes through its line"


@pytest.mark.parametrize("blow", ARM_BLOWS)
def test_the_full_blow_is_in_the_frame_and_the_fist_through(blow):
    slot = g.LIMB_SLOTS["arm-left" if g.BLOWS[blow]["arm"] == "left" else "arm-right"]
    posed = _posed(f"{blow}_strike", g.STRIKE_FULL)
    fist = pc.apply(posed[f"limb:{slot}:fist"].full(), (0.0, 0.0))
    x0, y0, x1, y1 = FRAME_BOX
    assert x0 + 100 <= fist[0] <= x1 - 100 and y0 + 100 <= fist[1] <= y1 - 100, f"{blow}: the fist is out of the frame: {fist}"
    assert _depth(blow, fist) > 70.0, f"{blow}: the fist is not through its line"


def test_every_arm_of_every_row_is_two_rigid_bones():
    """No arm is bent along its length or stretched: each is an upper arm and
    a forearm at their own lengths, joined at the elbow."""
    bad = []
    for anim, count, _ms in sg.ANIMATIONS:
        for phase in (0.0, 0.5):
            posed = _posed(anim, phase)
            assert not [n for n in posed if ":bone" in n or ":ink" in n], f"{anim}: a bending arm"
            for slot in ("hand_left", "hand_right"):
                upper, fore = posed.get(f"limb:{slot}:upper"), posed.get(f"limb:{slot}:fore")
                if upper is None or fore is None:
                    continue
                if abs(upper.stretch - 1.0) > 1e-6 or abs(fore.stretch - 1.0) > 1e-6:
                    bad.append(f"{anim} {slot}: stretched")
                end = pc.apply(upper.full(), (0.0, g.ARM_UPPER))
                start = pc.apply(fore.full(), (0.0, 0.0))
                if math.hypot(end[0] - start[0], end[1] - start[1]) > 0.5:
                    bad.append(f"{anim} {slot}: the elbow is apart")
    assert not bad, "\n".join(bad)


def _segments_cross(a, b, c, d):
    def orient(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    return orient(a, b, c) * orient(a, b, d) < 0 and orient(c, d, a) * orient(c, d, b) < 0


@pytest.mark.parametrize("blow", ARM_BLOWS)
def test_no_near_line_is_in_the_giants_own_body(blow):
    """A near line in the giant's body box (the box it collides with,
    `BODY_BBOX`) would take the giant through its own portal: each is out of
    it, by a margin."""
    x, y, w, h = g.BODY_BBOX
    box = (2.0 * (x - g.OFFSET[0]), 2.0 * (y - g.OFFSET[1]), 2.0 * (x + w - g.OFFSET[0]), 2.0 * (y + h - g.OFFSET[1]))
    margin = 12.0
    x0, y0, x1, y1 = box[0] - margin, box[1] - margin, box[2] + margin, box[3] + margin
    (cx, cy), (nx, ny) = g.BLOWS[blow]["line"]
    a, b = (cx + ny * HALF, cy - nx * HALF), (cx - ny * HALF, cy + nx * HALF)
    inside = lambda p: x0 <= p[0] <= x1 and y0 <= p[1] <= y1  # noqa: E731
    edges = [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
    assert not (inside(a) or inside(b) or any(_segments_cross(a, b, p, q) for p, q in edges)), (
        f"{blow}: its near line {a} to {b} is in the giant's body {box}")


#: The game's copy of the blows (`blows::limb`), when the renderer is checked
#: out in the game's tree.
CHOREOGRAPHY = Path(__file__).resolve().parents[3] / "game" / "ambition_content_modules" / "src" / "gnu_ton" / "choreography.rs"


@pytest.mark.skipif(not CHOREOGRAPHY.exists(), reason="the renderer is not checked out in the game's tree")
def test_the_game_types_the_near_lines_the_drawing_derives():
    """The game types each near line again (`blows::limb`): a line the drawing
    derives anew and the game does not take is an opening the arm misses."""
    src = CHOREOGRAPHY.read_text()
    body = src[src.index("pub const fn limb("):]
    body = body[:body.index("\n    }\n")]
    pair = r"Vec2::new\((-?[\d.]+), (-?[\d.]+)\)"
    typed = {(float(x), float(y)) for x, y in re.findall(r"line: " + pair, body)}
    normals = {(float(x), float(y)) for x, y in re.findall(r"normal: " + pair, body)}
    for blow, line in g.blow_lines_world()["blows"].items():
        at = tuple(round(v, 2) for v in line["at"])
        normal = tuple(round(v, 3) + 0.0 for v in line["normal"])
        assert any(math.dist(at, t) < 0.02 for t in typed), f"{blow}: the game does not type its line at {at}: {sorted(typed)}"
        assert normal in normals, f"{blow}: the game does not type its normal {normal}: {sorted(normals)}"
