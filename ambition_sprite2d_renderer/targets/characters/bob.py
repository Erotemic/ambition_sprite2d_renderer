"""SVG-rigged fighter target for Bob, the cryptography crew's engineer.

Bob is the conventional receiver of cryptography examples, personified as the
hardware engineer at the other end of Alice's channel, and a main character
and platform-fighter roster member in Ambition. He fights with a big
adjustable wrench (his reach), throws sealed packets from his satchel,
recovers on a telescoping antenna mast, and counters by *receiving*: his
analyzer verifies what hits him and he answers it.

The SVG ``data/characters/bob/bob.svg`` owns the art and marks every joint;
``rigged/bob/bob_side.rig.json`` owns the skeleton and the clips, derived from
the SVG and authored as key poses by ``scripts/build_bob_rig.py`` (through
``rigbuild.creature_rig`` with the ``humanoid`` anatomy). The rows and their
fighter-category coverage live in ``_bob_motion.py``. This module owns only the
effects (keyed by the clips' ``fx.*`` channels), the hit volumes (measured from
the wrench where the clips swing it) and publication.

Effects are glyphs painted once and placed (``_creature_fx.Glyphs``), in SVG
units like the art, except the wrench smear and the antenna mast, which are
shaped by the pose of the frame they are drawn in.
"""

from __future__ import annotations

import argparse
import math
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from PIL import Image

from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.portrait import FaceGuide, PortraitClip, render_framed_portrait, write_portrait_sheet
from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet
from . import _creature_fx as FX
from ._svg_fighter_effects import FxCanvas, compose_rig_frame
from ._bob_motion import BOB_ROWS, EFFECT_ALIASES, FIGHTER_MOTION_COVERAGE

Point = Tuple[float, float]
RGBA = Tuple[int, int, int, int]

TARGET_NAME = "bob"
RIG_PATH = Path(__file__).resolve().parent / "rigged" / "bob" / "bob_side.rig.json"
FRAME_SIZE = (360, 320)
#: Sprite pixels per SVG unit (the rig's ``svg_source.scale``).
ART_SCALE = 0.5
GROUND_Y = 569.0 * ART_SCALE
ROWS: List[Tuple[str, int, int]] = list(BOB_ROWS)

#: The wrench in its hand bone's frame (sprite pixels): the grip, a point
#: up the handle, the head, the jaw tips. The handle runs up the hand's -y.
WRENCH_GRIP = (4.5, 0.0)
WRENCH_MID = (4.5, -26.0)
WRENCH_HEAD = (4.5, -54.0)
WRENCH_TIP = (4.5, -64.0)
#: Where the smear's inner edge runs (most of a swing's sweep is the head).
WRENCH_TRAIL_INNER = (4.5, -38.0)
#: The analyzer's screen in the far hand's frame.
ANALYZER = (10.0, -5.0)


def _doc() -> RigDocument:
    return FX.rig_document(RIG_PATH)


# --- effect glyphs (SVG units) ------------------------------------------------------

WHITE = (255, 255, 255, 255)
SPARK = (255, 226, 112, 255)
SPARK_HOT = (255, 168, 60, 255)
CHARGE = (255, 196, 84, 255)
SHIELD_FILL = (120, 196, 255, 84)
SHIELD_EDGE = (186, 232, 255, 220)
SHIELD_SHINE = (240, 250, 255, 200)
CYAN = (90, 228, 214, 255)
CYAN_SOFT = (90, 228, 214, 120)
GREEN = (120, 236, 120, 255)
PAPER = (246, 236, 208, 255)
PAPER_DARK = (196, 178, 140, 255)
BRASS = (217, 156, 62, 255)
INK = (20, 17, 15, 255)
DIRT = (110, 82, 56, 255)
DIRT_DARK = (78, 56, 38, 255)
DIRT_LIGHT = (146, 112, 78, 255)
STEEL = (195, 201, 207, 255)
STEEL_DARK = (93, 102, 112, 255)
GOLD = (255, 214, 92, 255)


def _spark(c: FxCanvas) -> None:
    c.star((0, 0), 40.0, SPARK_HOT, points=8, inner=0.32, rotation=-90)
    c.star((0, 0), 28.0, SPARK, points=8, inner=0.4, rotation=-67.5)
    c.star((0, 0), 12.0, WHITE, points=4, inner=0.45, rotation=0)


def _glint(c: FxCanvas) -> None:
    c.star((0, 0), 16.0, WHITE, points=4, inner=0.22, rotation=0)
    c.ellipse((0, 0), 3.5, 3.5, WHITE)


def _charge(c: FxCanvas) -> None:
    c.ellipse((0, 0), 30, 30, None, (255, 196, 84, 150), 6.0)
    c.ellipse((0, 0), 20, 20, None, (255, 238, 170, 220), 2.5)
    for k in range(6):
        a = math.radians(k * 60.0 + 15.0)
        r0, r1 = 34.0, 46.0 + 6.0 * (k % 2)
        c.line([(r0 * math.cos(a), r0 * math.sin(a)), (r1 * math.cos(a), r1 * math.sin(a))], CHARGE, 2.6)


def _shield(c: FxCanvas) -> None:
    c.ellipse((0, 0), 132, 150, SHIELD_FILL)
    c.ellipse((0, 0), 132, 150, None, SHIELD_EDGE, 4.0)
    c.arc((0, 0), 112, 130, 200, 250, SHIELD_SHINE, 6.0)


def _shield_flash(c: FxCanvas) -> None:
    c.ellipse((0, 0), 138, 156, None, WHITE, 9.0)


def _shield_break(c: FxCanvas) -> None:
    for k in range(9):
        a = math.radians(k * 40.0 + 10.0)
        r = 150.0 + 18.0 * (k % 3)
        x, y = r * math.cos(a), r * math.sin(a)
        nx, ny = math.cos(a), math.sin(a)
        c.polygon([(x - ny * 14, y + nx * 14), (x + nx * 26, y + ny * 26), (x + ny * 12, y - nx * 12)],
                  SHIELD_EDGE, (255, 255, 255, 220), 1.5)
    c.star((0, 0), 60.0, WHITE, points=6, inner=0.3, rotation=-90)


def _parry(c: FxCanvas) -> None:
    c.ellipse((0, 0), 46, 46, None, (190, 240, 255, 230), 5.0)
    c.star((0, 0), 52.0, WHITE, points=6, inner=0.22, rotation=-90)
    c.star((0, 0), 22.0, CYAN, points=6, inner=0.4, rotation=-60)


def _tech(c: FxCanvas) -> None:
    c.ellipse((0, 0), 60, 60, None, (255, 255, 255, 200), 4.0)
    c.star((0, 0), 34.0, WHITE, points=4, inner=0.25, rotation=45)


def _packet(c: FxCanvas) -> None:
    # A sealed packet: an envelope with a brass padlock seal.
    c.polygon([(-24, -16), (24, -16), (24, 16), (-24, 16)], PAPER, INK, 2.2)
    c.line([(-24, -16), (0, 4), (24, -16)], PAPER_DARK, 2.0)
    c.ellipse((0, 6), 8, 7, BRASS, INK, 1.6)
    c.arc((0, 0), 5, 6, 180, 360, INK, 1.8)


def _whirl(c: FxCanvas) -> None:
    for r, a in ((70.0, 150), (56.0, 110), (40.0, 80)):
        c.ellipse((0, 0), r, r, None, (230, 240, 255, a), 7.0)
    c.arc((0, 0), 70, 70, 300, 360, WHITE, 3.0)
    c.arc((0, 0), 70, 70, 120, 180, WHITE, 3.0)


def _speed(c: FxCanvas) -> None:
    for y, length, a in ((-60, 120, 170), (-24, 160, 200), (12, 110, 170), (48, 140, 150), (80, 90, 130)):
        c.line([(-length, y), (0, y)], (255, 255, 255, a), 3.0)


def _verify(c: FxCanvas) -> None:
    c.ellipse((0, 0), 34, 34, None, CYAN_SOFT, 6.0)
    c.ellipse((0, 0), 24, 24, None, CYAN, 2.4)
    c.arc((0, 0), 44, 44, 300, 420, CYAN, 3.0)
    c.arc((0, 0), 44, 44, 120, 240, CYAN, 3.0)


def _check(c: FxCanvas) -> None:
    c.ellipse((0, 0), 30, 30, (20, 60, 40, 220), GREEN, 3.0)
    c.line([(-14, 0), (-4, 11), (16, -12)], GREEN, 6.0)


def _burst(c: FxCanvas) -> None:
    c.star((0, 0), 170.0, (255, 214, 92, 150), points=12, inner=0.3, rotation=-90)
    c.star((0, 0), 120.0, (255, 240, 180, 220), points=12, inner=0.35, rotation=-75)
    c.ellipse((0, 0), 52, 52, WHITE)


def _key(c: FxCanvas) -> None:
    # A key: ring bow, shaft, two bits.
    c.ellipse((-20, 0), 11, 11, None, GOLD, 5.0)
    c.line([(-9, 0), (24, 0)], GOLD, 5.0)
    c.line([(14, 0), (14, 9)], GOLD, 4.0)
    c.line([(22, 0), (22, 7)], GOLD, 4.0)


def _lock_open(c: FxCanvas) -> None:
    c.polygon([(-26, -6), (26, -6), (26, 34), (-26, 34)], BRASS, INK, 2.5)
    c.arc((-6, -6), 18, 22, 180, 360, STEEL, 6.0)
    c.ellipse((0, 12), 5, 5, INK)
    c.line([(0, 14), (0, 24)], INK, 3.0)


def _star(c: FxCanvas) -> None:
    c.star((0, 0), 10.0, GOLD, points=5, inner=0.45, rotation=-90, outline=INK)


def _zzz(c: FxCanvas) -> None:
    c.text((0, 0), "Z", (230, 240, 255, 255), size=26.0, stroke=INK)


def _alert(c: FxCanvas) -> None:
    c.text((0, 0), "!", (255, 220, 80, 255), size=40.0, stroke=INK)


def _mound(c: FxCanvas) -> None:
    # Churned earth heaped round a buried fighter (pivot on the ground line).
    c.polygon([(-120, 34), (-104, -10), (-70, -34), (-24, -44), (30, -42), (76, -30), (108, -8), (122, 34)],
              DIRT, INK, 2.5)
    c.polygon([(-96, -8), (-62, -28), (-20, -36), (26, -34), (68, -24), (94, -6), (40, -16), (-30, -18)], DIRT_LIGHT)
    for (x, y, r) in ((-60, 6, 8), (-10, 14, 10), (44, 4, 7), (84, 16, 6)):
        c.ellipse((x, y), r, r * 0.7, DIRT_DARK)


def _bubbles(c: FxCanvas) -> None:
    for (x, y, r) in ((0, 0, 7), (10, -20, 5), (-4, -38, 4), (8, -54, 3)):
        c.ellipse((x, y), r, r, None, (200, 236, 255, 220), 1.6)


def _sight(c: FxCanvas) -> None:
    for k in range(6):
        x = 14.0 + k * 26.0
        c.line([(x, 0), (x + 14, 0)], (255, 120, 100, 200), 2.2)
    c.ellipse((170, 0), 10, 10, None, (255, 120, 100, 220), 2.2)


def _zap(c: FxCanvas) -> None:
    pts = [(0, 0), (30, -10), (52, 6), (84, -8), (108, 8), (140, -4), (176, 4)]
    c.line(pts, CYAN_SOFT, 12.0)
    c.line(pts, CYAN, 5.0)
    c.line(pts, WHITE, 2.0)
    c.star((176, 4), 18.0, WHITE, points=4, inner=0.3, rotation=0)


def _waves(c: FxCanvas) -> None:
    for r, a in ((24, 240), (42, 200), (60, 150)):
        c.arc((0, 0), r, r, 220, 320, (90, 228, 214, a), 4.0)


def _blink(c: FxCanvas) -> None:
    for (x, y, r) in ((-60, -150, 10), (40, -170, 8), (70, -90, 12), (-80, -40, 9), (30, -20, 11), (-20, -110, 7),
                      (80, 10, 8), (-50, 40, 10), (10, 70, 7), (60, 100, 9)):
        c.star((x, y), r, (200, 250, 255, 255), points=4, inner=0.25, rotation=0)


GLYPHS = FX.Glyphs(
    ART_SCALE,
    {
        **FX.COMMON,
        "spark": ((44.0, 44.0, 44.0, 44.0), _spark),
        "glint": ((18.0, 18.0, 18.0, 18.0), _glint),
        "charge": ((50.0, 50.0, 50.0, 50.0), _charge),
        "shield": ((138.0, 156.0, 138.0, 156.0), _shield),
        "shield_flash": ((146.0, 164.0, 146.0, 164.0), _shield_flash),
        "shield_break": ((200.0, 200.0, 200.0, 200.0), _shield_break),
        "parry": ((56.0, 56.0, 56.0, 56.0), _parry),
        "tech": ((64.0, 64.0, 64.0, 64.0), _tech),
        "packet": ((28.0, 20.0, 28.0, 20.0), _packet),
        "whirl": ((76.0, 76.0, 76.0, 76.0), _whirl),
        "speed": ((164.0, 66.0, 4.0, 86.0), _speed),
        "verify": ((50.0, 50.0, 50.0, 50.0), _verify),
        "check": ((34.0, 34.0, 34.0, 34.0), _check),
        "burst": ((172.0, 172.0, 172.0, 172.0), _burst),
        "key": ((34.0, 14.0, 28.0, 14.0), _key),
        "lock_open": ((30.0, 32.0, 30.0, 38.0), _lock_open),
        "star": ((12.0, 12.0, 12.0, 12.0), _star),
        "zzz": ((20.0, 20.0, 20.0, 20.0), _zzz),
        "alert": ((20.0, 28.0, 20.0, 28.0), _alert),
        "mound": ((126.0, 48.0, 126.0, 40.0), _mound),
        "bubbles": ((12.0, 60.0, 16.0, 10.0), _bubbles),
        "sight": ((4.0, 14.0, 184.0, 14.0), _sight),
        "zap": ((6.0, 22.0, 196.0, 22.0), _zap),
        "waves": ((64.0, 64.0, 64.0, 8.0), _waves),
        "blink": ((96.0, 184.0, 96.0, 112.0), _blink),
    },
)
_place = GLYPHS.place
_local = GLYPHS.local


# --- where effects sit ------------------------------------------------------------------


def _foot_ground(world, side: str) -> Point:
    ankle = world[f"{side}_foot"].origin
    return (ankle[0] + 8.0, min(GROUND_Y - 1.0, ankle[1] + 9.0))


def _body_centre(world) -> Point:
    return world["torso"].to_world((50.0, 0.0))


def _wrench_shown(params) -> bool:
    return params.get("prop.wrench", 1.0) > 0.5


def _swing_samples(doc: RigDocument, animation: str, t: float, frame_count: int, steps: int = 8,
                   span: float = 1.0):
    """The near hand's world over the last ``span`` of the frame interval
    leading up to ``t`` (oldest first): the rig is keyed between frames for
    swings, so these follow the authored arc."""
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
        if _wrench_shown(params):
            out.append(world["near_hand"])
    return out


def _trail(canvas: FxCanvas, hands, strength: float) -> None:
    """The wrench smear: the arc the head swept between the last frame and
    this one, as a band that fades toward where the wrench was."""
    if len(hands) < 2:
        return
    outer = [h.to_world(WRENCH_TIP) for h in hands]
    inner = [h.to_world(WRENCH_TRAIL_INNER) for h in hands]
    span = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(outer, outer[1:]))
    if span < 6.0:
        return
    n = len(outer) - 1
    for k in range(n):
        a = int(150 * min(1.0, strength) * (k + 1) / n)
        if a < 8:
            continue
        canvas.polygon([outer[k], outer[k + 1], inner[k + 1], inner[k]], (226, 238, 255, a))
    canvas.line(outer[n // 2:], (255, 255, 255, int(220 * min(1.0, strength))), 2.0)


def _mast(canvas: FxCanvas, world, extend: float) -> None:
    """The telescoping antenna mast from the ground up to Bob's boots."""
    feet = min(world["near_foot"].origin[1], world["far_foot"].origin[1]) + 10.0
    x = (world["near_foot"].origin[0] + world["far_foot"].origin[0]) * 0.5 + 6.0
    top = GROUND_Y - (GROUND_Y - feet) * min(1.0, extend)
    if GROUND_Y - top < 4.0:
        return
    h = GROUND_Y - top
    for k, half in enumerate((7.0, 5.0, 3.5)):
        y0 = GROUND_Y - h * k / 3.0
        y1 = GROUND_Y - h * (k + 1) / 3.0
        canvas.polygon([(x - half, y0), (x + half, y0), (x + half, y1), (x - half, y1)], STEEL, INK, 1.2)
        canvas.line([(x - half + 1.5, y0 - 1), (x - half + 1.5, y1 + 1)], WHITE, 1.0)
    canvas.polygon([(x - 18, GROUND_Y), (x + 18, GROUND_Y), (x + 10, GROUND_Y - 7), (x - 10, GROUND_Y - 7)],
                   STEEL_DARK, INK, 1.2)
    canvas.polygon([(x - 16, top), (x + 16, top), (x + 12, top + 5), (x - 12, top + 5)], BRASS, INK, 1.2)


# --- the frame ---------------------------------------------------------------------------


def _behind(animation: str, frame_count: int):
    def draw(canvas: FxCanvas, t: float, world, params) -> None:
        doc = _doc()
        trail = params.get("fx.trail", 0.0)
        if trail > 0.02 and _wrench_shown(params):
            _trail(canvas, _swing_samples(doc, animation, t, frame_count), trail)
        shield = params.get("fx.shield", 0.0)
        if shield > 0.02:
            _place(canvas, "shield", _body_centre(world), 0.8 * shield)
        speed = params.get("fx.speed", 0.0)
        if speed > 0.02:
            vertical = animation in ("antenna_launch", "air_down")
            at = _local(world["pelvis"], -60.0, -10.0) if not vertical else world["pelvis"].origin
            degrees = 0.0 if not vertical else (90.0 if animation == "antenna_launch" else -90.0)
            if vertical:
                at = (at[0], at[1] + (70.0 if animation == "antenna_launch" else -90.0) * ART_SCALE)
            _place(canvas, "speed", at, speed, degrees)
        for key, deg in (("fx.launch", 160.0), ("fx.meteor", -100.0)):
            v = params.get(key, 0.0)
            if v > 0.02:
                _place(canvas, "speed", _body_centre(world), v, deg)
        mast = params.get("fx.mast", 0.0)
        if mast > 0.02:
            _mast(canvas, world, mast)
        final = params.get("fx.final", 0.0)
        if final > 0.25:
            centre = (world["pelvis"].origin[0] + 90.0, world["pelvis"].origin[1] - 50.0)
            _place(canvas, "burst", centre, min(1.0, (final - 0.25) / 0.35), 30.0 * t)
        blink = params.get("fx.blink", 0.0)
        if blink > 0.02:
            _place(canvas, "blink", world["pelvis"].origin, blink)
    return draw


def _front(animation: str, frame_count: int):
    def draw(canvas: FxCanvas, t: float, world, params) -> None:
        hand = world["near_hand"]
        if _wrench_shown(params):
            spark = params.get("fx.spark", 0.0)
            if spark > 0.02:
                _place(canvas, "spark", hand.to_world(WRENCH_HEAD), spark, 22.5 * (round(t * 8) % 2))
            charge = params.get("fx.charge", 0.0)
            if charge > 0.02:
                _place(canvas, "charge", hand.to_world(WRENCH_HEAD), charge, 360.0 * t)
            glint = params.get("fx.glint", 0.0)
            if glint > 0.02:
                _place(canvas, "glint", hand.to_world(WRENCH_TIP), glint, 45.0 * t)
            whirl = params.get("fx.whirl", 0.0)
            if whirl > 0.02:
                _place(canvas, "whirl", hand.to_world((4.5, -32.0)), whirl * 0.85, 720.0 * t)
        far = world["far_hand"]
        for key, glyph in (("fx.dust", "dust"),):
            v = params.get(key, 0.0)
            if v > 0.02:
                _place(canvas, glyph, _foot_ground(world, "near"), v)
                _place(canvas, glyph, _foot_ground(world, "far"), 0.8 * v)
        trail_dust = params.get("fx.dust_trail", 0.0)
        if trail_dust > 0.02:
            x, y = _foot_ground(world, "far")
            _place(canvas, "dust", (x - 22.0, y), trail_dust)
            _place(canvas, "dust", (x - 44.0, y + 1.0), 0.6 * trail_dust)
        wall = params.get("fx.wall_dust", 0.0)
        if wall > 0.02:
            _place(canvas, "dust", world["near_foot"].to_world((16.0, 0.0)), wall)
        for key, side in (("fx.shock", 1.0), ("fx.shock_back", -1.0)):
            v = params.get(key, 0.0)
            if v > 0.02:
                if side > 0 and _wrench_shown(params):
                    x = hand.to_world(WRENCH_HEAD)[0]
                else:
                    x = world["pelvis"].origin[0] + side * 55.0
                _place(canvas, "shock", (x, GROUND_Y), v)
        stomp = params.get("fx.stomp", 0.0)
        if stomp > 0.02:
            _place(canvas, "shock", _foot_ground(world, "near"), stomp)
        hit = params.get("fx.hit", 0.0)
        if hit > 0.02:
            _place(canvas, "hit", _body_centre(world), hit)
        flash = params.get("fx.shield_flash", 0.0)
        if flash > 0.02:
            _place(canvas, "shield_flash", _body_centre(world), flash)
        broke = params.get("fx.shield_break", 0.0)
        if broke > 0.02:
            _place(canvas, "shield_break", _body_centre(world), broke)
        parry = params.get("fx.parry", 0.0)
        if parry > 0.02:
            _place(canvas, "parry", hand.to_world(WRENCH_MID), parry)
        tech = params.get("fx.tech", 0.0)
        if tech > 0.02:
            _place(canvas, "tech", _body_centre(world), tech)
        hold = params.get("fx.packet_hold", 0.0)
        if hold > 0.02:
            _place(canvas, "packet", far.to_world((8.0, 0.0)), hold)
        packet = params.get("fx.packet", 0.0)
        if 0.0 < packet < 0.999:
            x0, y0 = _packet_release()
            x = x0 + 64.0 * packet
            y = y0 - 14.0 * math.sin(math.pi * packet) + 6.0 * packet
            _place(canvas, "packet", (x, y), 1.0 if packet < 0.75 else (1.0 - packet) / 0.25, 25.0 * packet)
        toss = max(params.get("fx.toss", 0.0), params.get("fx.tap", 0.0))
        if toss > 0.02:
            _place(canvas, "glint", far.to_world((12.0, 0.0)), toss)
        if params.get("prop.analyzer", 0.0) > 0.5:
            screen = far.to_world(ANALYZER)
            verify = params.get("fx.verify", 0.0)
            if verify > 0.02:
                _place(canvas, "verify", screen, verify * (0.65 + 0.35 * math.cos(math.tau * 2.0 * t)), 90.0 * t)
            counter = params.get("fx.counter", 0.0)
            if counter > 0.02:
                _place(canvas, "check", (screen[0], screen[1] - 22.0), counter)
            for key in ("fx.analyzer_charge",):
                v = params.get(key, 0.0)
                if v > 0.02:
                    _place(canvas, "verify", screen, v, 180.0 * t)
            aim = params.get("fx.aim", 0.0)
            if aim > 0.02:
                _place(canvas, "sight", (screen[0] + 8.0, screen[1]), 0.8 * aim)
            zap = params.get("fx.zap", 0.0)
            if zap > 0.02:
                _place(canvas, "zap", (screen[0] + 8.0, screen[1]), zap)
            waves = params.get("fx.waves", 0.0)
            if waves > 0.02:
                _place(canvas, "waves", (screen[0], screen[1] - 14.0), waves * (0.7 + 0.3 * math.sin(math.tau * 3 * t)))
        final = params.get("fx.final", 0.0)
        if final > 0.25:
            centre = (world["pelvis"].origin[0] + 90.0, world["pelvis"].origin[1] - 50.0)
            reach = 30.0 + 60.0 * min(1.0, final)
            for k in range(3):
                a = math.tau * (k / 3.0 + 0.6 * t)
                _place(canvas, "key", (centre[0] + reach * math.cos(a), centre[1] + reach * math.sin(a)),
                       min(1.0, (final - 0.25) / 0.2), math.degrees(a))
            _place(canvas, "lock_open", centre, min(1.0, (final - 0.4) / 0.2) if final > 0.4 else 0.0)
        head_top = world["head"].tip
        stars = params.get("fx.stars", 0.0)
        if stars > 0.02:
            for k in range(3):
                a = math.tau * (k / 3.0 + t)
                _place(canvas, "star", (head_top[0] + 22.0 * math.cos(a), head_top[1] - 6.0 + 7.0 * math.sin(a)),
                       stars, 72.0 * k)
        zzz = params.get("fx.zzz", 0.0)
        if animation == "sleep":
            for k in range(3):
                u = (t + k / 3.0) % 1.0
                _place(canvas, "zzz", (head_top[0] + 10.0 + 14.0 * u, head_top[1] - 8.0 - 30.0 * u),
                       math.sin(math.pi * u), -10.0)
        elif zzz > 0.02:
            _place(canvas, "zzz", (head_top[0] + 12.0, head_top[1] - 14.0), zzz, -10.0)
        alert = params.get("fx.alert", 0.0)
        if alert > 0.02:
            _place(canvas, "alert", (head_top[0] + 6.0, head_top[1] - 22.0), alert)
        if params.get("fx.bubbles", 0.0) > 0.0 or animation == "swim":
            u = t % 1.0
            _place(canvas, "bubbles", (head_top[0] + 14.0, head_top[1] - 6.0 - 10.0 * u), 0.9 * math.sin(math.pi * u))
        bury = params.get("fx.bury", 0.0)
        if bury > 0.02:
            _place(canvas, "mound", (world["pelvis"].origin[0] + 4.0, GROUND_Y), bury)
    return draw


@lru_cache(maxsize=1)
def _packet_release() -> Point:
    """Where the packet leaves the far hand (``packet_toss`` at t = 0.556)."""
    world, _params = _doc().solve("packet_toss", 5.0 / 9.0)
    return world["far_hand"].to_world((12.0, 0.0))


def render_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    return compose_rig_frame(
        _doc(),
        animation,
        frame_idx,
        frame_count,
        behind=_behind(animation, frame_count),
        front=_front(animation, frame_count),
        fx_pieces=True,
    )


# --- hit volumes --------------------------------------------------------------------------

#: The wrench's outline in its hand's frame (sprite pixels), for hit volumes.
WRENCH_HULL = ((-2.0, -14.0), (11.0, -14.0), (-7.0, -46.0), (16.0, -46.0), (-6.0, -66.0), (15.0, -66.0))
#: Effects that make a frame of a row active, and the bone + points that hit.
_STRIKE_FX = ("fx.trail", "fx.whirl")


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


@lru_cache(maxsize=1)
def attack_hitboxes() -> Dict[str, dict]:
    """Every row that swings the wrench (or stamps a boot) gets the volume it
    actually sweeps on its active frames: the wrench outline at each frame
    and through the interval before it, hulled. Measured from the rig, so the
    volume a player is hit by is the arc they are shown."""
    doc = _doc()
    out: Dict[str, dict] = {}
    for name, frames, _ms in ROWS:
        clip = doc.clips.get(name) or {}
        if bool(clip.get("loop", True)):
            continue
        active, points = [], []
        for i in range(frames):
            t = doc.frame_time(name, i, frames)
            world, params = doc.solve(name, t)
            wrench = _wrench_shown(params) and (
                max(params.get(k, 0.0) for k in _STRIKE_FX) >= 0.5 or params.get("fx.spark", 0.0) >= 0.75
            )
            stomp = params.get("fx.stomp", 0.0) >= 0.75
            if not (wrench or stomp):
                continue
            # A sweep already under way counts its whole approach; the first
            # active frame only the last 30% of it (strikes snap in from an
            # eased wind-up, so before that the wrench is still loading
            # behind or above him).
            span = 1.0 if active and active[-1] == i - 1 else 0.3
            active.append(i)
            if wrench:
                for hand in _swing_samples(doc, name, t, frames, steps=4, span=span) or [world["near_hand"]]:
                    points += [hand.to_world(p) for p in WRENCH_HULL]
            if stomp:
                foot = world["near_foot"]
                points += [foot.to_world(p) for p in ((-10.0, -12.0), (26.0, -12.0), (-10.0, 10.0), (26.0, 10.0))]
        if not active:
            continue
        poly = [(round(x, 2), round(y, 2)) for x, y in _hull(points)]
        xs, ys = [p[0] for p in poly], [p[1] for p in poly]
        x0, y0 = int(math.floor(min(xs))), int(math.floor(min(ys)))
        x1, y1 = int(math.ceil(max(xs))), int(math.ceil(max(ys)))
        out[name] = {"active_frames": active, "bbox": (x0, y0, x1 - x0, y1 - y0), "poly": poly}
    return out


def _window(row: str) -> List[dict]:
    """Hitbox start / end events for a row, from its measured active frames."""
    box = attack_hitboxes().get(row)
    frames = next(n for name, n, _ms in ROWS if name == row)
    if not box:
        return []
    first, last = box["active_frames"][0], box["active_frames"][-1]
    src = "explicit.profile.bob"
    return [
        {"t": round(first / frames, 3), "event": "hitbox_active_start", "source": src},
        {"t": round(min(1.0, (last + 1) / frames), 3), "event": "hitbox_active_end", "source": src},
    ]


# --- the actor -----------------------------------------------------------------------------


def _pt(p: Point) -> Dict[str, float]:
    return {"x": round(p[0], 1), "y": round(p[1], 1)}


@lru_cache(maxsize=1)
def _sockets() -> Dict[str, dict]:
    doc = _doc()
    world, _ = doc.solve("idle", 0.0)
    aim, _ = doc.solve("aim", 0.0)
    head = world["head"]
    src = "explicit.profile.bob"
    muzzle = aim["far_hand"].to_world((22.0, -5.0))
    return {
        "head": {"source": src, "point": _pt(head.to_world((head.length * 0.5, 0.0)))},
        "chest": {"source": src, "point": _pt(world["torso"].to_world((world["torso"].length * 0.62, 0.0)))},
        "hand_l": {"source": src, "point": _pt(world["far_hand"].origin)},
        "hand_r": {"source": src, "point": _pt(world["near_hand"].origin)},
        "speech_bubble": {"source": src, "point": _pt((head.tip[0], head.tip[1] - 16.0))},
        "muzzle": {"source": src, "point": _pt(muzzle)},
        "projectile_origin": {"source": src, "point": _pt(_packet_release())},
        "wrench_head": {"source": src, "point": _pt(world["near_hand"].to_world(WRENCH_HEAD))},
    }


#: The gameplay body (published frame pixels): torso and legs, head to
#: boots, not the wrench or a swinging arm.
BODY_BOX = {"x": 142, "y": 94, "w": 46, "h": 191}
FEET = (170.0, GROUND_Y)


def body_metrics(fw: int, fh: int) -> dict:
    return {
        "body_pixel_bbox": dict(BODY_BOX),
        "feet_pixel": {"x": FEET[0], "y": FEET[1]},
        "feet_anchor_norm": {"x": round(FEET[0] / fw - 0.5, 6), "y": round(0.5 - FEET[1] / fh, 6)},
    }


def _bind(row: str, events: bool = False) -> dict:
    return {"animation": row, "events": _window(row) if events else []}


def _bindings() -> Dict[str, dict]:
    b = {
        "default": _bind("idle"),
        "locomotion.walk": _bind("walk"),
        "locomotion.run": _bind("run"),
        "traversal.jump": _bind("jump"),
        "traversal.fall": _bind("fall"),
        # The procedural Bob's sheet bound these names; kept so nothing that
        # read them goes dark.
        "locomotion.jump": _bind("jump"),
        "locomotion.fall": _bind("fall"),
        "locomotion.crouch": _bind("crouch"),
        "locomotion.land": _bind("land"),
        "locomotion.swim": _bind("swim"),
        "locomotion.climb": _bind("climb"),
        "locomotion.wall_slide": _bind("wall_slide"),
        "locomotion.wall_jump": _bind("wall_jump"),
        "locomotion.ledge_grab": _bind("ledge_grab"),
        "locomotion.ledge_climb": _bind("ledge_climb"),
        "interaction.talk": _bind("talk"),
        "interaction.use": _bind("interact"),
        "action.melee.primary": _bind("jab", True),
        "action.melee.forward": _bind("attack_side", True),
        "action.melee.up": _bind("attack_up", True),
        "action.melee.down": _bind("attack_down", True),
        "action.melee.dash": _bind("dash_attack", True),
        "action.smash.forward": _bind("smash_forward", True),
        "action.smash.up": _bind("smash_up", True),
        "action.smash.down": _bind("smash_down", True),
        "action.aerial.neutral": _bind("air_neutral", True),
        "action.aerial.forward": _bind("air_forward", True),
        "action.aerial.back": _bind("air_back", True),
        "action.aerial.up": _bind("air_up", True),
        "action.aerial.down": _bind("air_down", True),
        "action.special.neutral": {
            "animation": "packet_toss",
            "events": [{"t": 0.556, "event": "projectile_release", "source": "explicit.profile.bob"}],
        },
        "action.special.side": _bind("torque_rush", True),
        "action.special.up": _bind("antenna_launch"),
        "action.special.down": _bind("receive"),
        "action.special.final": _bind("full_handshake"),
        "action.capture.grab": _bind("grab"),
        "action.capture.pummel": _bind("pummel", True),
        "action.capture.throw_forward": _bind("throw_forward", True),
        "action.capture.throw_back": _bind("throw_back", True),
        "action.capture.throw_up": _bind("throw_up", True),
        "action.capture.throw_down": _bind("throw_down", True),
        "action.defense.block": _bind("block"),
        "action.defense.roll": _bind("roll"),
        "action.defense.parry": _bind("parry"),
        "action.ranged.primary": {
            "animation": "shoot",
            "events": [{"t": 0.33, "event": "projectile_release", "source": "explicit.profile.bob"}],
        },
        "damage.hit": _bind("hit"),
        "lifecycle.death": _bind("death"),
        "emote.taunt": _bind("taunt"),
        "emote.victory": _bind("celebrate"),
    }
    # The bespoke specials under the generic primary / secondary names too.
    b["action.special.primary"] = b["action.special.neutral"]
    b["action.special.secondary"] = b["action.special.side"]
    return b


ACTOR_METADATA = {
    "actor": {"character_id": "npc_bob", "display_name": "Bob"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": ["story", "humanoid", "engineer", "fighter", "svg_rigged"],
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
        "interactions": {"talk": True, "trade": None, "carry": True, "open_doors": ["public"]},
    },
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "peaceful"},
    "visual": {
        "default_pose": "idle",
        "canonical_source": "ambition_sprite2d_renderer/data/characters/bob/bob.svg",
        "portrait": {
            "face_guide": {
                "center": {"x": 182.0, "y": 120.0},
                "size": {"width": 48.0, "height": 50.0},
                "source_size": {"width": FRAME_SIZE[0], "height": FRAME_SIZE[1]},
            }
        },
    },
    "tags": ["story", "humanoid", "engineer", "player_candidate", "fighter", "svg_rigged"],
    "authoring_description": (
        "Bob is the conventional receiver in cryptography examples, personified as the engineer "
        "waiting at the other end of Alice's channel. His apparent passivity is the joke: receiving an "
        "authentic message that only he can open is a technically and emotionally demanding role. "
        "Drawn as a stocky, bearded hardware engineer: safety glasses pushed up on his forehead, a "
        "rolled-sleeve work shirt under a tan utility vest with a hi-vis band, a leather satchel, a "
        "keyring at his belt, work boots, and a big adjustable wrench."
    ),
    "gameplay_description": (
        "A grounded mid-weight bruiser with a long, heavy reach. His wrench carries a three-hit jab "
        "string, tilts, smashes that load visibly before they land, and aerials (a whirling neutral "
        "air and a spiking forward air). His specials are an engineer's kit: a sealed packet tossed "
        "from his satchel (neutral), a drill-spun wrench rush (side), a telescoping antenna mast that "
        "launches him (up), and receive (down), a counter in which his analyzer verifies what hits "
        "him and he answers it. His final smash is the full handshake. Outside a fight he is a "
        "receiver, engineer, cooperative partner, or endpoint tutorial NPC."
    ),
    "dialogue_hints": {
        "barks": [
            "I receive. Alice sends, I get it.",
            "Try receiving a message you can't open and tell me it's passive.",
            "The roles are just where you're standing in the sentence.",
        ]
    },
    "motion": {
        "fighter_coverage": dict(FIGHTER_MOTION_COVERAGE),
        "effect_aliases": dict(EFFECT_ALIASES),
    },
}


def _finish_metadata() -> None:
    ACTOR_METADATA["sockets"] = _sockets()
    ACTOR_METADATA["animation_bindings"] = _bindings()


# --- publication ------------------------------------------------------------------------------

FACE = FaceGuide(
    center_x=182.0,
    center_y=120.0,
    width=48.0,
    height=50.0,
    source_width=FRAME_SIZE[0],
    source_height=FRAME_SIZE[1],
)


def render_portraits(out_dir: Path, **opts) -> List[Path]:
    """Dialog portraits rerendered from the rig at 4x, never the sheet."""
    del opts
    doc = _doc()

    def frame(animation: str, index: int, count: int) -> Image.Image:
        source = doc.render_at(animation, doc.frame_time(animation, index, count), supersample=2, scale=4)
        return render_framed_portrait(source, FACE, view_width=78.0, center_y=124.0)

    clips = {
        "default": PortraitClip.loop(tuple(frame("idle", i, 8) for i in range(8)), duration_ms=140),
        "portrait": PortraitClip.still(frame("idle_front", 6, 8)),
        "talking": PortraitClip.loop(tuple(frame("talk", i, 8) for i in range(8)), duration_ms=104),
        "determined": PortraitClip.still(frame("smash_forward_charge", 0, 6)),
        "verifying": PortraitClip.still(frame("receive", 4, 10)),
        "hurt": PortraitClip.still(frame("hit", 1, 5)),
        "pleased": PortraitClip.still(frame("victory_hold", 0, 8)),
    }
    return write_portrait_sheet(TARGET_NAME, clips, Path(out_dir), still_clip="portrait")


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    _finish_metadata()
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        auto_crop=False,
        actor_metadata=ACTOR_METADATA,
        body_metrics_fn=body_metrics,
        pose_bodies="authored",
        # Bob stands ~188 px in a 320 px frame (59%); the procedural Bob
        # stood 206 px in 253 (81%) at the runtime's default scale of 1.5.
        # Assuming the runtime sizes the frame from the collision height,
        # 2.08 keeps him the size he was on screen.
        sheet_tuning={"collision_scale": 2.08},
        animation_key_map={name: name for name, _frames, _ms in ROWS},
        attack_hitboxes=attack_hitboxes(),
    )
    parts = publish_rig_flipbook(TARGET_NAME, ROWS, render_frame, outputs, frame_transform, out_dir)
    keys = ("spritesheet", "yaml", "ron", "actor", "preview", "canonical", "canonical_transparent")
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


__all__ = [
    "ACTOR_METADATA", "FIGHTER_MOTION_COVERAGE", "ROWS", "TARGET_NAME", "attack_hitboxes", "render",
    "render_frame", "render_portraits",
]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path,
                        default=Path(__file__).resolve().parents[2] / "generated" / TARGET_NAME)
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
