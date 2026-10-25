"""Alice, v2: the cryptographer who sends, made by the character generator.

Alice is the conventional sender of cryptography examples, personified as a
courier and cartographer, Bob's partner at the other end of the channel. The
first Alice (``alice_cryptographer``) is a side-view puppet; this one is drawn
by ``chargen`` from ONE 3D description, so she has every view: front, front
three-quarter, side, back three-quarter and back, and their mirrors (eight
angles), in every pose of her sheet.

* Her spec: ``data/characters/alice_v2/alice_v2.chargen.yaml`` (her body,
  face, coat, boots and colours).
* Her own gear: ``_alice_v2_gear.py`` (her bob, the pencil on her ear, the map
  tube, the cipher wheel, the range pole and the sealed letter), drawn into
  the same SVG and rigs through ``chargen.extras``.
* Her motion: ``_alice_v2_motion.py`` (her rows and her own clips on the
  generator's pose kit; the library's for the rest).
* This module: the rigs, the effects her clips key (``fx.*``), the hit
  volumes measured from the pole, the actor sidecar, and publication.

The sheet keeps every row name of the first Alice sheet, so the game can use
either by its manifest, and adds the rows her moveset asks for (``jab``, the
smashes, her specials, the grab and throws). Effects are glyphs painted once
and placed (``_creature_fx.Glyphs``), in centimetres; none is a drop shadow
and none is a portal (the game draws the portals of her up special).
"""

from __future__ import annotations

import argparse
import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import yaml
from PIL import Image

from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.portrait import FaceGuide, PortraitClip, render_framed_portrait, write_portrait_sheet
from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet
from ...chargen import extras
from ...chargen.body import build as build_figure
from ...chargen.geometry import VIEWS
from ...chargen.motion import solve_clip
from ...chargen.pose3d import ViewSolver
from ...chargen.rig import CELL_H, CELL_W, PX_PER_CM, build_rigs, character_svg, slug
from ...chargen.spec import CharacterSpec, complete
from . import _creature_fx as FX
from ._alice_v2_gear import POLE_BUTT, POLE_LENGTH, alice_parts
from ._alice_v2_motion import CONTRACT_ROWS, MOVESET_ROWS, ROWS, alice_library
from ._svg_fighter_effects import FxCanvas, compose_rig_frame

Point = Tuple[float, float]

TARGET_NAME = "alice_v2"
SPEC_PATH = Path(__file__).resolve().parents[2] / "data" / "characters" / "alice_v2" / "alice_v2.chargen.yaml"
#: Her rig frame (base pixels, published at the rig's ``render_scale``): wide
#: and tall enough for the pole at full reach in front, behind and overhead.
FRAME_W, FRAME_H, FRAME_CX, FRAME_GROUND = 320, 340, 160.0, 286.0
#: The pole in base frame pixels.
CM = PX_PER_CM


def load_spec() -> CharacterSpec:
    return complete(yaml.safe_load(SPEC_PATH.read_text(encoding="utf8")))


# ---- the rigs -------------------------------------------------------------------------------------


def _clips(fig, view, doc) -> Dict[str, dict]:
    """Her rows, solved for one view's rig."""
    lib = alice_library(fig)
    solver = ViewSolver(fig, view, doc, PX_PER_CM)
    return {name: solve_clip(lib[name], solver) for name in ROWS}


def _with_room_for_the_pole(svg: str) -> str:
    """The multiview SVG with one empty cell more on its right.

    At rest the pole runs forward and up from her fist, past the right edge
    of its view's cell. A part is drawn only where the canvas is, so in the
    last view (the back) the canvas cut the pole's head off. The empty cell
    gives it room; no view moves (each rig has its own pixel origin)."""
    w = CELL_W * len(VIEWS)
    old = f'width="{w:g}mm" height="{CELL_H:g}mm" viewBox="0 0 {w:g} {CELL_H:g}"'
    new = f'width="{w + CELL_W:g}mm" height="{CELL_H:g}mm" viewBox="0 0 {w + CELL_W:g} {CELL_H:g}"'
    if old not in svg:
        raise ValueError("the multiview SVG is not sized as chargen.rig writes it")
    return svg.replace(old, new, 1)


def build(out_dir: Path) -> Dict[str, Path]:
    """Her multiview SVG and one rig per view in ``out_dir``; the rigs, by
    view key."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    spec = load_spec()
    name = slug(spec.name) + "_v2"
    svg_path = out_dir / f"{name}.svg"
    with extras.using(alice_parts):
        svg_path.write_text(_with_room_for_the_pole(character_svg(spec)), encoding="utf8")
        rigs = build_rigs(spec, svg_path, out_dir, clips=_clips, grip="staff")
    views = {name: clip.view for name, clip in alice_library(build_figure(spec)).items() if name in ROWS}
    for key, path in rigs.items():
        doc = json.loads(path.read_text(encoding="utf8"))
        fr = doc["frame"]
        fr.update(width=FRAME_W, height=FRAME_H, center_x=FRAME_CX, ground_y=FRAME_GROUND)
        doc["chargen"]["publish_views"] = views
        path.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf8")
    return rigs


# ---- effect glyphs (centimetres) ----------------------------------------------------------------------

WHITE = (255, 255, 255, 255)
INK = (29, 23, 20, 255)
TEAL = (86, 196, 196, 255)
TEAL_SOFT = (86, 196, 196, 110)
AMBER = (242, 190, 92, 255)
AMBER_HOT = (226, 140, 52, 255)
ROUTE = (204, 74, 64, 255)
PAPER = (243, 231, 196, 255)
PAPER_DARK = (203, 184, 138, 255)
BRASS = (217, 156, 62, 255)


def _spark(c: FxCanvas) -> None:
    # Gold and teal, as the first Alice's blows: a ring round a star.
    c.ellipse((0, 0), 8.5, 8.5, None, TEAL, 0.9)
    c.star((0, 0), 9.0, AMBER_HOT, points=8, inner=0.34, rotation=-90)
    c.star((0, 0), 6.0, AMBER, points=8, inner=0.4, rotation=-67.5)
    c.star((0, 0), 2.8, WHITE, points=4, inner=0.45, rotation=0)


def _compass(c: FxCanvas) -> None:
    # The first Alice's neutral air: a gold ring and a teal ring, each in
    # four arcs, and three red route stops between them.
    for radius, color, width in ((40.0, AMBER, 1.4), (31.0, TEAL, 1.1)):
        for k in range(4):
            c.arc((0, 0), radius, radius, 90 * k, 90 * k + 70, color, width)
    for k in range(3):
        a = math.radians(120.0 * k + 30.0)
        c.ellipse((36.0 * math.cos(a), 36.0 * math.sin(a)), 2.2, 2.2, ROUTE, INK, 0.35)


def _burst(c: FxCanvas) -> None:
    c.star((0, 0), 18.0, (242, 190, 92, 150), points=12, inner=0.32, rotation=-90)
    c.star((0, 0), 12.0, (255, 240, 190, 230), points=12, inner=0.36, rotation=-75)
    c.ellipse((0, 0), 4.5, 4.5, WHITE)
    # A cipher ring round the burst: her hardest blows are signed.
    c.ellipse((0, 0), 15.0, 15.0, None, TEAL, 0.9)
    for k in range(12):
        a = math.radians(k * 30.0)
        c.line([(13.5 * math.cos(a), 13.5 * math.sin(a)), (16.5 * math.cos(a), 16.5 * math.sin(a))], TEAL, 0.7)


def _shield(c: FxCanvas) -> None:
    # A ward drawn like a compass rose round her: a ring, its ticks, and
    # the four points. Not a bubble of glass: a map's bearing.
    c.ellipse((0, 0), 30.0, 50.0, (86, 196, 196, 96))
    c.ellipse((0, 0), 30.0, 50.0, None, (180, 236, 230, 235), 2.2)
    for k in range(16):
        a = math.radians(k * 22.5)
        r0 = 0.88 if k % 4 else 0.78
        c.line([(30.0 * r0 * math.cos(a), 50.0 * r0 * math.sin(a)), (30.0 * math.cos(a), 50.0 * math.sin(a))], (180, 236, 230, 220), 0.7)
    c.arc((0, 0), 26.0, 45.0, 200, 250, (240, 250, 255, 200), 1.6)


def _charge(c: FxCanvas) -> None:
    # The cipher wheel turning: a ring of ticks, a brass rim.
    c.ellipse((0, 0), 8.5, 8.5, None, (242, 190, 92, 170), 1.6)
    c.ellipse((0, 0), 5.5, 5.5, None, (86, 196, 196, 220), 0.8)
    for k in range(12):
        a = math.radians(k * 30.0)
        c.line([(9.5 * math.cos(a), 9.5 * math.sin(a)), (11.5 * math.cos(a), 11.5 * math.sin(a))], AMBER, 0.8)


def _cast(c: FxCanvas) -> None:
    # A survey triangle, its corners pinned, a route through it.
    pts = [(14.0 * math.cos(math.radians(a)), 14.0 * math.sin(math.radians(a))) for a in (-90, 30, 150)]
    c.line(pts + [pts[0]], AMBER, 1.0)
    for p in pts:
        c.ellipse(p, 1.5, 1.5, ROUTE, INK, 0.3)
    c.line([pts[2], (0.0, 0.0), pts[1]], TEAL, 0.7)
    c.ellipse((0, 0), 4.0, 4.0, None, TEAL, 0.7)


def _sight(c: FxCanvas) -> None:
    for k in range(7):
        x = 4.0 + k * 9.0
        c.line([(x, 0), (x + 5.0, 0)], (204, 74, 64, 210), 0.7)
    c.ellipse((72.0, 0), 3.2, 3.2, None, (204, 74, 64, 230), 0.7)
    c.line([(72.0, -5.0), (72.0, 5.0)], (204, 74, 64, 230), 0.5)
    c.line([(67.0, 0.0), (77.0, 0.0)], (204, 74, 64, 230), 0.5)


def _dart(c: FxCanvas) -> None:
    # A route pin in flight: a red head, a steel point, a dashed trail.
    for k in range(4):
        c.line([(-30.0 + k * 7.0, 0), (-26.0 + k * 7.0, 0)], (255, 255, 255, 170), 0.8)
    c.polygon([(0.0, -2.0), (7.0, 0.0), (0.0, 2.0)], (200, 206, 212, 255), INK, 0.3)
    c.ellipse((-1.5, 0.0), 2.6, 2.6, ROUTE, INK, 0.4)


def _pin(c: FxCanvas) -> None:
    # A map pin driven into the floor (the pivot is its point).
    c.line([(0.0, 0.0), (0.0, -8.0)], (200, 206, 212, 255), 0.9)
    c.ellipse((0.0, -10.0), 3.0, 3.0, ROUTE, INK, 0.45)
    c.ellipse((0.0, 0.0), 9.0, 2.2, None, (255, 232, 170, 220), 0.7)


def _key(c: FxCanvas) -> None:
    c.ellipse((-6.0, 0.0), 3.0, 3.0, None, BRASS, 1.3)
    c.line([(-3.0, 0.0), (7.0, 0.0)], BRASS, 1.3)
    c.line([(4.0, 0.0), (4.0, 2.4)], BRASS, 1.1)
    c.line([(6.5, 0.0), (6.5, 2.0)], BRASS, 1.1)


def _letter(c: FxCanvas) -> None:
    c.polygon([(-5.0, -3.4), (5.0, -3.4), (5.0, 3.4), (-5.0, 3.4)], PAPER, INK, 0.45)
    c.line([(-5.0, -3.4), (0.0, 0.6), (5.0, -3.4)], PAPER_DARK, 0.45)
    c.ellipse((0.0, 0.8), 1.2, 1.2, ROUTE, INK, 0.3)


def _whirl(c: FxCanvas) -> None:
    for r, a in ((34.0, 120), (28.0, 90)):
        c.arc((0, 0), r, r, 0, 300, (230, 240, 255, a), 2.2)
    c.arc((0, 0), 34.0, 34.0, 250, 300, WHITE, 1.0)


def _speed(c: FxCanvas) -> None:
    for y, length, a in ((-38, 34, 170), (-20, 46, 200), (-2, 30, 170), (16, 40, 150), (32, 26, 130)):
        c.line([(-length, y), (0, y)], (255, 255, 255, a), 0.9)


def _route(c: FxCanvas) -> None:
    # Her blink: a dotted route drawn round where she stands, its stops in
    # red. A map's line, not a door; the game takes her body apart.
    pts = [(-16.0, 20.0), (-20.0, -4.0), (-8.0, -28.0), (8.0, -46.0), (20.0, -24.0), (14.0, 2.0), (22.0, 26.0)]
    for a, b in zip(pts, pts[1:]):
        for k in range(3):
            u0, u1 = k / 3.0, k / 3.0 + 0.18
            c.line([(a[0] + (b[0] - a[0]) * u0, a[1] + (b[1] - a[1]) * u0), (a[0] + (b[0] - a[0]) * u1, a[1] + (b[1] - a[1]) * u1)],
                   (86, 196, 196, 230), 0.9)
    for p in pts[::2]:
        c.ellipse(p, 1.8, 1.8, ROUTE, INK, 0.3)


GLYPHS = FX.Glyphs(
    CM,
    {
        **FX.COMMON,
        "spark": ((10.0, 10.0, 10.0, 10.0), _spark),
        "burst": ((19.0, 19.0, 19.0, 19.0), _burst),
        "shield": ((32.0, 52.0, 32.0, 52.0), _shield),
        "charge": ((12.5, 12.5, 12.5, 12.5), _charge),
        "cast": ((15.0, 15.0, 15.0, 15.0), _cast),
        "sight": ((1.0, 6.0, 78.0, 6.0), _sight),
        "dart": ((32.0, 4.0, 8.0, 4.0), _dart),
        "pin": ((10.0, 14.0, 10.0, 3.0), _pin),
        "key": ((10.0, 4.0, 8.0, 4.0), _key),
        "letter": ((6.0, 4.5, 6.0, 4.5), _letter),
        "whirl": ((36.0, 36.0, 36.0, 36.0), _whirl),
        "compass": ((42.0, 42.0, 42.0, 42.0), _compass),
        "speed": ((48.0, 40.0, 2.0, 34.0), _speed),
        "route": ((23.0, 48.0, 23.0, 28.0), _route),
    },
)
_place = GLYPHS.place


# ---- the pole, in its bone's frame ------------------------------------------------------------------


@lru_cache(maxsize=8)
def _pole_local(rig_path: str) -> Dict[str, Point]:
    """The pole's tip, middle, butt and a point a third of the way down from
    the tip, in the ``near_grip`` bone's frame (base frame pixels): read off
    the rest pose, where the pole runs forward and ``ITEM_REST_ANGLE`` up."""
    from ...chargen.draw import ITEM_REST_ANGLE

    doc = RigDocument.load(Path(rig_path))
    probe = RigDocument(dict(doc.data, clips={}))
    world, _ = probe.solve("", 0.0, sampled_channels={})
    g = world["near_grip"]
    a = math.radians(-ITEM_REST_ANGLE)
    d = (math.cos(a), math.sin(a))
    r = math.radians(-g.angle)

    def local(s_cm: float) -> Point:
        wx, wy = d[0] * s_cm * CM, d[1] * s_cm * CM
        return (wx * math.cos(r) - wy * math.sin(r), wx * math.sin(r) + wy * math.cos(r))

    tip = POLE_LENGTH - POLE_BUTT
    return {"tip": local(tip + 4.0), "inner": local(tip * 0.78), "mid": local(tip * 0.5), "butt": local(-POLE_BUTT), "grip": local(0.0)}


def _pole_shown(params) -> bool:
    return params.get("prop.staff", 1.0) > 0.5


def _samples(doc: RigDocument, animation: str, t: float, frame_count: int, steps: int = 6, span: float = 1.0):
    """The near grip's world over the frame interval before ``t``, oldest
    first (for a swing's smear and its hit volume)."""
    clip = doc.clips.get(animation) or {}
    if bool(clip.get("loop", True)) or frame_count < 2:
        return []
    dt = span / (frame_count - 1)
    out = []
    for k in range(steps, -1, -1):
        tk = t - dt * k / steps
        if tk < 0.0:
            continue
        world, params = doc.solve(animation, tk)
        if _pole_shown(params):
            out.append(world["near_grip"])
    return out


def _trail(canvas: FxCanvas, grips, pole: Dict[str, Point], strength: float) -> None:
    """The smear the pole's point swept since the last frame: a teal band
    from where the point was to where it is, faded toward where it was, its
    edge gold. It ends at the point; nothing is drawn ahead of it."""
    if len(grips) < 2:
        return
    outer = [g.to_world(pole["tip"]) for g in grips]
    inner = [g.to_world(pole["inner"]) for g in grips]
    span = sum(math.dist(a, b) for a, b in zip(outer, outer[1:]))
    if span < 4.0:
        return
    n = len(outer) - 1
    for k in range(n):
        a = int(150 * min(1.0, strength) * (k + 1) / n)
        if a >= 8:
            canvas.polygon([outer[k], outer[k + 1], inner[k + 1], inner[k]], (150, 222, 216, a))
    canvas.line(outer[n // 2:], (242, 200, 110, int(230 * min(1.0, strength))), 0.9)


def _effects(doc: RigDocument, rig_path: str, animation: str, frame_count: int):
    pole = _pole_local(rig_path)

    def body(world) -> Point:
        return world["torso"].origin if "torso" in world else world["pelvis"].origin

    def feet(world) -> Point:
        a, b = world["near_leg_foot"].origin, world["far_leg_foot"].origin
        return ((a[0] + b[0]) / 2.0, float(doc.frame["ground_y"]) - 1.0)

    def behind(canvas: FxCanvas, t: float, world, params) -> None:
        trail = params.get("fx.trail", 0.0)
        if trail > 0.02 and _pole_shown(params):
            _trail(canvas, _samples(doc, animation, t, frame_count), pole, trail)
        shield = params.get("fx.shield", 0.0)
        if shield > 0.02:
            _place(canvas, "shield", body(world), 0.85 * shield)
        speed = params.get("fx.speed", 0.0)
        if speed > 0.02:
            c = body(world)
            _place(canvas, "speed", (c[0] - 20.0 * CM, c[1]), speed)
        blink = params.get("fx.blink", 0.0)
        if blink > 0.02:
            _place(canvas, "route", body(world), blink)
        whirl = params.get("fx.whirl", 0.0)
        if whirl > 0.02:
            _place(canvas, "whirl", body(world), 0.8 * whirl, 360.0 * t)
        compass = params.get("fx.compass", 0.0)
        if compass > 0.02:
            _place(canvas, "compass", body(world), compass, 160.0 * t)

    def front(canvas: FxCanvas, t: float, world, params) -> None:
        g = world["near_grip"]
        tip = g.to_world(pole["tip"])
        if _pole_shown(params):
            for key, glyph, k in (("fx.spark", "spark", 1.0), ("fx.burst", "burst", 1.0)):
                v = params.get(key, 0.0)
                if v > 0.02:
                    _place(canvas, glyph, tip, k * v, 22.5 * (round(t * 8) % 2))
            charge = params.get("fx.charge", 0.0)
            if charge > 0.02:
                _place(canvas, "charge", tip, charge, 360.0 * t)
            cast = params.get("fx.cast", 0.0)
            if cast > 0.02:
                ux, uy = tip[0] - g.origin[0], tip[1] - g.origin[1]
                n = math.hypot(ux, uy) or 1.0
                _place(canvas, "cast", (tip[0] + ux / n * 16.0 * CM, tip[1] + uy / n * 16.0 * CM), cast, 90.0 * t)
            aim = params.get("fx.aim", 0.0)
            if aim > 0.02:
                _place(canvas, "sight", tip, 0.85 * aim)
            dart = params.get("fx.dart", 0.0)
            if dart > 0.02:
                _place(canvas, "dart", (tip[0] + 30.0 * CM * dart, tip[1]), min(1.0, 1.6 * (1.0 - abs(2.0 * dart - 1.0)) + 0.3))
            pin = params.get("fx.pin", 0.0)
            if pin > 0.02:
                _place(canvas, "pin", (tip[0], float(doc.frame["ground_y"]) - 1.0), pin)
            key = params.get("fx.key", 0.0)
            if key > 0.02:
                _place(canvas, "key", (tip[0] + 6.0 * CM, tip[1] - 8.0 * CM), key, -20.0)
        dust = params.get("fx.dust", 0.0)
        if dust > 0.02:
            _place(canvas, "dust", feet(world), dust)
        letter = params.get("fx.letter", 0.0)
        if letter > 0.02:
            h = world["far_grip"].origin
            _place(canvas, "letter", (h[0] + 14.0 * CM * letter, h[1] - 2.0 * CM * letter), letter, -10.0 * letter)

    return behind, front


# ---- the sheet ---------------------------------------------------------------------------------------


class AliceSheet:
    """Her rigs, rendered as sheet rows: each row from the view its clip
    names, with her effects."""

    def __init__(self, rigs: Dict[str, Path], rows: Sequence[str] = ROWS) -> None:
        self.paths = {k: str(Path(p).resolve()) for k, p in rigs.items()}
        self.docs = {k: RigDocument.load(Path(p)) for k, p in self.paths.items()}
        some = next(iter(self.docs.values()))
        self.views: Dict[str, str] = dict(some.data["chargen"]["publish_views"])
        self.names = list(rows)

    def doc_of(self, row: str, view: Optional[str] = None) -> Tuple[RigDocument, str]:
        key = view or self.views.get(row, "side")
        return self.docs[key], self.paths[key]

    def rows(self) -> List[Tuple[str, int, int]]:
        out = []
        for name in self.names:
            c = self.doc_of(name)[0].clips[name]
            out.append((name, int(c["frames"]), int(c["duration_ms"])))
        return out

    def frame_size(self) -> Tuple[int, int]:
        fr = next(iter(self.docs.values())).frame
        k = int(fr.get("render_scale", 1))
        return int(fr["width"]) * k, int(fr["height"]) * k

    def render_frame(self, animation: str, frame_idx: int, frame_count: int, view: Optional[str] = None) -> Image.Image:
        doc, path = self.doc_of(animation, view)
        behind, front = _effects(doc, path, animation, frame_count)
        return compose_rig_frame(doc, animation, frame_idx, frame_count, behind=behind, front=front, fx_pieces=True)


# ---- hit volumes ------------------------------------------------------------------------------------

#: Effects that make a frame of a row active.
_STRIKE_FX = ("fx.trail", "fx.spark")


def _hull(points: Sequence[Point]) -> List[Point]:
    pts = sorted(set((round(x, 1), round(y, 1)) for x, y in points))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: List[Point] = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: List[Point] = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def attack_hitboxes(sheet: AliceSheet) -> Dict[str, dict]:
    """Each row that strikes with the pole gets the volume the pole sweeps on
    its active frames (published frame pixels): the pole's outline at each
    frame and through the interval before it, hulled. Measured from the rig,
    so the volume she hits with is the arc she is shown swinging."""
    out: Dict[str, dict] = {}
    for name, frames, _ms in sheet.rows():
        doc, path = sheet.doc_of(name)
        if bool(doc.clips[name].get("loop", True)):
            continue
        pole = _pole_local(path)
        k = int(doc.frame.get("render_scale", 1))
        r = 2.2 * CM
        hull_local = [(p[0] + dx, p[1] + dy) for p in (pole["tip"], pole["mid"]) for dx, dy in ((r, r), (r, -r), (-r, r), (-r, -r))]
        active, points = [], []
        for i in range(frames):
            t = doc.frame_time(name, i, frames)
            world, params = doc.solve(name, t)
            if not _pole_shown(params) or max(params.get(f, 0.0) for f in _STRIKE_FX) < 0.5:
                continue
            span = 1.0 if active and active[-1] == i - 1 else 0.3
            active.append(i)
            for g in _samples(doc, name, t, frames, steps=4, span=span) or [world["near_grip"]]:
                points += [g.to_world(p) for p in hull_local]
        if not active:
            continue
        poly = [(round(x * k, 2), round(y * k, 2)) for x, y in _hull(points)]
        xs, ys = [p[0] for p in poly], [p[1] for p in poly]
        x0, y0 = int(math.floor(min(xs))), int(math.floor(min(ys)))
        x1, y1 = int(math.ceil(max(xs))), int(math.ceil(max(ys)))
        out[name] = {"active_frames": active, "bbox": (x0, y0, x1 - x0, y1 - y0), "poly": poly}
    return out


# ---- the actor ---------------------------------------------------------------------------------------


def _bind(row: str, hits: Dict[str, dict], frames: Dict[str, int]) -> dict:
    box = hits.get(row)
    if not box:
        return {"animation": row, "events": []}
    first, last, n = box["active_frames"][0], box["active_frames"][-1], frames[row]
    src = "explicit.profile.alice_v2"
    return {"animation": row, "events": [{"t": round(first / n, 3), "event": "hitbox_active_start", "source": src},
                                         {"t": round(min(1.0, (last + 1) / n), 3), "event": "hitbox_active_end", "source": src}]}


def _bindings(hits: Dict[str, dict], frames: Dict[str, int]) -> Dict[str, dict]:
    b = {key: _bind(row, hits, frames) for key, row in (
        ("default", "idle"), ("locomotion.walk", "walk"), ("locomotion.run", "run"), ("locomotion.hover", "hover"),
        ("traversal.jump", "jump"), ("traversal.fall", "fall"), ("locomotion.crouch", "crouch"), ("locomotion.land", "land"),
        ("locomotion.swim", "swim"), ("locomotion.climb", "climb"), ("locomotion.wall_slide", "wall_slide"),
        ("locomotion.wall_jump", "wall_jump"), ("locomotion.ledge_grab", "ledge_grab"), ("locomotion.ledge_climb", "ledge_climb"),
        ("interaction.talk", "talk"), ("interaction.use", "interact"),
        ("action.melee.primary", "jab"), ("action.melee.forward", "attack_side"), ("action.melee.up", "attack_up"),
        ("action.melee.down", "attack_down"), ("action.melee.dash", "dash_attack"), ("action.smash.forward", "smash_forward"),
        ("action.smash.up", "smash_up"), ("action.smash.down", "smash_down"), ("action.aerial.neutral", "air_neutral"),
        ("action.aerial.forward", "air_forward"), ("action.aerial.back", "air_back"), ("action.aerial.up", "air_up"),
        ("action.aerial.down", "air_down"), ("action.special.neutral", "one_time_pad"), ("action.special.side", "key_exchange"),
        ("action.special.up", "elliptic_curve"), ("action.special.down", "hash_collision"),
        ("action.special.air_down", "collision_dive"), ("action.capture.grab", "grab"), ("action.capture.pummel", "pummel"),
        ("action.capture.throw_forward", "throw_forward"), ("action.capture.throw_back", "throw_back"),
        ("action.capture.throw_up", "throw_up"), ("action.capture.throw_down", "throw_down"), ("action.defense.block", "block"),
        ("action.defense.roll", "roll"), ("damage.hit", "hit"), ("lifecycle.death", "death"), ("emote.taunt", "taunt"),
        ("emote.victory", "celebrate"))}
    b["action.ranged.primary"] = {"animation": "shoot", "events": [{"t": 0.5, "event": "projectile_release", "source": "explicit.profile.alice_v2"}]}
    b["action.special.primary"] = b["action.special.neutral"]
    b["action.special.secondary"] = b["action.special.side"]
    return b


ACTOR_METADATA = {
    # The same character as the first Alice: the game can swap her manifest.
    "actor": {"character_id": "npc_alice", "display_name": "Alice"},
    "body": {"body_plan": "HumanoidBiped", "body_kind": "Standard", "mass_class": "Medium",
             "traits": ["story", "humanoid", "intro", "cryptographer", "fighter", "generated"], "locomotion_hint": "Walk"},
    "capabilities": {
        "traversal": {"walk": True, "jump": True, "climb": True, "fly": None, "swim": True, "crawl": None, "use_lifts": True,
                      "door_access": ["public"]},
        "interactions": {"talk": True, "trade": None, "carry": None, "open_doors": ["public"]},
    },
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "peaceful"},
    "visual": {"default_pose": "idle", "canonical_source": "ambition_sprite2d_renderer/data/characters/alice_v2/alice_v2.chargen.yaml"},
    "tags": ["story", "humanoid", "intro", "cryptographer", "fighter", "generated", "svg_rigged"],
    "authoring_description": (
        "Alice is the conventional sender in cryptography and security examples, personified as a courier and cartographer: "
        "the textbook phrase 'Alice sends a message to Bob' made into a life spent carrying secrets through rooms that may be "
        "listening. She parodies no one. Version 2 redraws her on the character generator, so she has all eight views: a "
        "slim woman of 165 cm in an open knee-length teal coat with garnet piping and gold cuffs over a burgundy shirt and a "
        "garnet tie, slate trousers and maroon boots with turned-down cuffs and laces, a full navy bob with a side-swept fringe "
        "and a blue sheen under an amethyst Alice band, a garnet pin at her temple and garnet drop earrings, a leather satchel "
        "on her right hip, a brass cipher wheel at her belt with an amethyst hub, and a striped surveyor's range pole "
        "for her reach. Her sealed letters are for Bob."
    ),
    "gameplay_description": (
        "A reach-and-recovery fighter with a range pole: quick pokes, a long lunge, sweeps at the shins, a pole whirled round "
        "her in the air. Her specials follow her moveset: one-time pad (an armoured overhead blow), key exchange (she crosses "
        "the gap), elliptic curve (a rising cut, then the drop into the portals the game opens), hash collision (two pins in "
        "the floor, then a launch) and collision dive. Outside a fight she is the messenger who sends the player to Bob."
    ),
    "dialogue_hints": {"barks": ["Official maps are for people who enjoy being found.",
                                 "Carry this to Bob. Do not unfold it where the walls can read.",
                                 "There is always a someone in the middle."]},
}


# ---- publication ------------------------------------------------------------------------------------


def _face_guide(doc: RigDocument, fig, head=None) -> FaceGuide:
    """Her face in a view's frame (base pixels): at rest, or where ``head``
    (the head bone's world in a posed frame) carries it."""
    probe = RigDocument(dict(doc.data, clips={}))
    world, _ = probe.solve("", 0.0, sampled_channels={})
    from ...chargen.geometry import VIEW_BY_KEY

    # The middle of the head, from the neck joint the head bone turns about,
    # as this view projects it (in a side view the face is ahead of it).
    view = VIEW_BY_KEY[doc.data["chargen"]["view"]]
    nx, ny = view.project(fig.joints["neck"])
    cx, cy = view.project((0.0, fig.fy(0.5), 0.0))
    rest = world["head"]
    px, py = rest.origin[0] + (cx - nx) * CM, rest.origin[1] + (cy - ny) * CM
    if head is not None:
        r = math.radians(-rest.angle)
        dx, dy = px - rest.origin[0], py - rest.origin[1]
        px, py = head.to_world((dx * math.cos(r) - dy * math.sin(r), dx * math.sin(r) + dy * math.cos(r)))
    hh = fig.hh * CM
    return FaceGuide(center_x=px, center_y=py, width=hh * 0.95, height=hh * 1.05,
                     source_width=float(doc.frame["width"]), source_height=float(doc.frame["height"]))


def render_portraits(out_dir: Path, *, rigs: Optional[Dict[str, Path]] = None, **opts) -> List[Path]:
    """Dialog portraits rerendered from her rigs at 4x, never the sheet: the
    resting, speaking and focused portraits face the viewer (focused: she
    reads her letter); the reactions are side on, as Bob's are."""
    del opts
    out_dir = Path(out_dir)
    rigs = rigs or build(out_dir / "rig")
    sheet = AliceSheet(rigs)
    fig = build_figure(load_spec())

    def frame(animation: str, index: int, view: str) -> Image.Image:
        doc, _ = sheet.doc_of(animation, view)
        n = int(doc.clips[animation]["frames"])
        t = doc.frame_time(animation, index, n)
        source = doc.render_at(animation, t, supersample=2, scale=4)
        face = _face_guide(doc, fig, doc.solve(animation, t)[0]["head"])
        return render_framed_portrait(source, face, view_width=face.width * 1.9, center_y=face.center_y + face.height * 0.42)

    talk_n = int(sheet.doc_of("talk", "front")[0].clips["talk"]["frames"])
    idle_n = int(sheet.doc_of("idle_front", "front")[0].clips["idle_front"]["frames"])
    clips = {
        "default": PortraitClip.loop(tuple(frame("idle_front", i, "front") for i in range(idle_n)), duration_ms=150),
        "portrait": PortraitClip.still(frame("idle_front", 1, "front")),
        "speaking": PortraitClip.loop(tuple(frame("talk", i, "front") for i in range(talk_n)), duration_ms=105),
        "focused": PortraitClip.still(frame("interact", 2, "front")),
        "determined": PortraitClip.still(frame("smash_forward", 2, "side")),
        "hurt": PortraitClip.still(frame("hit", 1, "side")),
        "pleased": PortraitClip.still(frame("celebrate", 7, "front_3q")),
    }
    return write_portrait_sheet(TARGET_NAME, clips, out_dir, still_clip="portrait")


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rigs = build(out_dir / "rig")
    sheet = AliceSheet(rigs)
    hits = attack_hitboxes(sheet)
    frames = {name: n for name, n, _ms in sheet.rows()}
    meta = dict(ACTOR_METADATA, animation_bindings=_bindings(hits, frames))
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=sheet.rows(),
        render_fn=sheet.render_frame,
        out_dir=out_dir,
        frame_size=sheet.frame_size(),
        auto_crop=False,
        actor_metadata=meta,
        sheet_tuning={"collision_scale": 1.7},
        animation_key_map={name: name for name in sheet.names},
        attack_hitboxes=hits,
    )
    parts = publish_rig_flipbook(TARGET_NAME, sheet.rows(), sheet.render_frame, outputs, frame_transform, out_dir)
    keys = ("spritesheet", "yaml", "ron", "actor", "preview", "canonical", "canonical_transparent")
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


__all__ = ["ACTOR_METADATA", "CONTRACT_ROWS", "MOVESET_ROWS", "ROWS", "TARGET_NAME", "AliceSheet", "attack_hitboxes", "build", "load_spec",
           "render", "render_portraits"]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[2] / "generated" / TARGET_NAME)
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
