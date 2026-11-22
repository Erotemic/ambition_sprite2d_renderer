"""The Command Uplink: the Supreme Leader's link to his network in the War
Room (`docs/planning/game/bosses.md`, "The Supreme Leader"). He calls it down
and gives his orders through it; it fires them.

An iron mast on a stepped base, a crimson banner with the regime's sigil
down its front, two emitter pods on its face (the low one by the base, the
high one at the height a jump reaches), and a dish at the top with a crimson
lens in a turning gold ring. Struck, it sparks; broken, its lens bursts and
the mast folds.

Rows: ``idle`` 8 (the lens breathes, the ring turns); ``charge`` 8 (both
pods and the lens brighten: an order is coming); ``fire`` 6 (the pods
blaze); ``drop`` 8 (it comes down from above on its tether and lands);
``hurt`` 3; ``death`` 12 (the lens bursts, sparks, the mast folds, smoke;
the last frame the wreck).

Facing right; it is the same from either side. The base stands on
``FLOOR``. The pods are at :data:`LOW_POD` and :data:`HIGH_POD` frame pixels
over the floor (the conductor's lines leave them).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import List, Tuple

from PIL import Image

from ...authoring.sheet_build import build_sheet
from .supreme_leader import (CRIMSON, CRIMSON_DARK, GOLD, GOLD_DARK, GOLD_LIGHT, ORB, ORB_LIGHT, OUTLINE, SUPER, Pen,
                             _a, _glow, _mix, _s, _sigil)

TARGET_NAME = "command_uplink"
FRAME_SIZE = (200, 360)
FLOOR = 340.0
#: The pods' heights over the floor, in frame pixels: 2 frame pixels to a
#: world unit, so the low line runs 22 units over the floor and the high
#: one 104.
LOW_POD = 44.0
HIGH_POD = 208.0
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 110),
    ("charge", 8, 80),
    ("fire", 6, 60),
    ("drop", 8, 60),
    ("hurt", 3, 80),
    ("death", 12, 90),
]

IRON = (70, 66, 76, 255)
IRON_LIGHT = (112, 108, 122, 255)
IRON_DARK = (40, 38, 46, 255)
SMOKE = (60, 56, 62, 255)
SPARK = (255, 236, 170, 255)


@dataclass(frozen=True)
class State:
    glow: float = 0.3
    pods: float = 0.0
    ring: float = 0.0
    drop: float = 0.0
    hurt: float = 0.0
    broken: float = 0.0
    sparks: float = -1.0
    smoke: float = 0.0


def draw_uplink(st: State) -> Image.Image:
    work = Image.new("RGBA", (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER), (0, 0, 0, 0))
    pen = Pen(work)
    cx = FRAME_SIZE[0] / 2.0
    lift = -260.0 * st.drop
    fold = st.broken
    floor = FLOOR + lift

    def at(x: float, h: float) -> Tuple[float, float]:
        # The mast folds over from its middle as it breaks.
        if h > 150.0 and fold > 0.0:
            ang = math.radians(28.0 * fold)
            dx, dy = x, h - 150.0
            return (cx + dx * math.cos(ang) + dy * math.sin(ang), floor - 150.0 - (dy * math.cos(ang) - dx * math.sin(ang)) + 10 * fold)
        return (cx + x, floor - h)

    # The tether it comes down on.
    if st.drop > 0.0:
        pen.line([at(0, 300), (cx, 0.0)], IRON_DARK, 3.0)
    # The stepped base.
    pen.poly([at(-46, 0), at(46, 0), at(40, 18), at(-40, 18)], IRON_DARK, 1.4)
    pen.poly([at(-34, 18), at(34, 18), at(30, 30), at(-30, 30)], IRON, 1.4)
    pen.line([at(-44, 4), at(44, 4)], IRON_LIGHT, 1.2)
    # The mast.
    pen.poly([at(-16, 30), at(16, 30), at(12, 250), at(-12, 250)], IRON, 1.5)
    pen.line([at(-10, 34), at(-8, 246)], IRON_LIGHT, 1.6)
    for h in (80.0, 140.0, 190.0):
        pen.poly([at(-15, h - 3), at(15, h - 3), at(15, h + 3), at(-15, h + 3)], IRON_DARK, 0.8)
    # The banner down its front.
    sway = math.sin(st.ring * 6.28) * 2.0
    pen.poly([at(-14, 236), at(14, 236), at(14 + sway, 70), at(0, 58), at(-14 + sway, 70)], CRIMSON, 1.2)
    pen.line([at(-11, 236), at(-11 + sway, 72)], CRIMSON_DARK, 1.6)
    pen.line([at(10, 234), at(10 + sway, 72)], GOLD, 1.2)
    _sigil(pen, at(0 + sway * 0.5, 196), 10.0)
    # The pods: the low one by the base, the high one on the mast.
    # A pod each side, so it fires down the room whichever end it stands at.
    for h in (LOW_POD, HIGH_POD):
        for sx in (1.0, -1.0):
            pen.poly([at(sx * 8, h - 9), at(sx * 24, h - 9), at(sx * 30, h - 5), at(sx * 30, h + 5), at(sx * 24, h + 9),
                      at(sx * 8, h + 9)], IRON_DARK, 1.2)
            lens = at(sx * 30, h)
            k = max(0.0, min(1.0, st.pods))
            if k > 0.05:
                _glow(work, lambda d, p=lens: d.ellipse([*_s((p[0] - 16 * k, p[1] - 16 * k)), *_s((p[0] + 16 * k, p[1] + 16 * k))],
                                                        fill=_a(ORB, 0.7 * k)), 4.0)
            pen.circle(lens, 4.6, _mix(CRIMSON_DARK, ORB_LIGHT, k), 1.0)
    # The dish and the lens in its turning ring.
    pen.poly([at(-30, 250), at(30, 250), at(22, 264), at(-22, 264)], IRON_DARK, 1.4)
    if fold < 0.6:
        pen.ellipse(at(0, 282), 22.0, 22.0, None, 0)
        ring_rx = 22.0 * abs(math.cos(st.ring * 6.28)) + 4.0
        pen.ellipse(at(0, 282), ring_rx, 22.0, None, 2.8, GOLD)
        pen.ellipse(at(0, 282), 22.0, 22.0, None, 2.0, GOLD_DARK)
        g = max(0.0, min(1.0, st.glow))
        _glow(work, lambda d: d.ellipse([*_s((at(0, 282)[0] - 24, at(0, 282)[1] - 24)), *_s((at(0, 282)[0] + 24, at(0, 282)[1] + 24))],
                                        fill=_a(ORB, 0.6 * g)), 6.0)
        pen.circle(at(0, 282), 11.0, _mix(CRIMSON_DARK, ORB, 0.4 + 0.6 * g), 1.2)
        pen.circle(at(-3, 285), 3.6, _mix(ORB, ORB_LIGHT, g), 0)
    else:
        # The lens is gone: a black socket and torn ring.
        pen.circle(at(0, 282), 10.0, IRON_DARK, 1.2)
        pen.line([at(-20, 272), at(-10, 296)], GOLD_DARK, 2.4)
        pen.line([at(18, 270), at(8, 300)], GOLD_DARK, 2.4)
    pen.poly([at(-3, 300), at(3, 300), at(0, 312)], GOLD, 0.8)
    if st.hurt > 0.0:
        _glow(work, lambda d: d.rectangle([*_s((cx - 30, floor - 300)), *_s((cx + 30, floor))], fill=_a((255, 255, 255, 255), 0.35 * st.hurt)), 3.0)
    if st.sparks >= 0.0:
        u = st.sparks
        for i in range(12):
            a = i * 2.4 + 0.6
            r = 10.0 + 60.0 * u
            p = (at(0, 282)[0] + math.cos(a) * r, at(0, 282)[1] + math.sin(a) * r + 40.0 * u * u)
            pen.circle(p, max(0.6, 3.0 * (1.0 - u)), _a(SPARK, 1.0 - u), 0)
        if u < 0.4:
            _glow(work, lambda d: d.ellipse([*_s((at(0, 282)[0] - 50, at(0, 282)[1] - 50)), *_s((at(0, 282)[0] + 50, at(0, 282)[1] + 50))],
                                            fill=_a(GOLD_LIGHT, 0.8 * (1.0 - u / 0.4))), 8.0)
    if st.smoke > 0.0:
        for i in range(5):
            u = (st.smoke + i * 0.2) % 1.0
            p = (at(0, 270)[0] + math.sin(i * 1.9) * 12.0, at(0, 270)[1] - 70.0 * u)
            pen.circle(p, 8.0 + 14.0 * u, _a(SMOKE, 0.5 * (1.0 - u) * min(1.0, st.smoke * 3)), 0)
    return work.resize(FRAME_SIZE, Image.LANCZOS)


def _state_for(animation: str, i: int, n: int) -> State:
    loop = animation in ("idle", "charge", "fire")
    t = i / n if loop else i / max(1, n - 1)
    if animation == "idle":
        return State(glow=0.35 + 0.15 * math.sin(t * 6.28), ring=t)
    if animation == "charge":
        return State(glow=0.6 + 0.3 * math.sin(t * 12.56), pods=0.5 + 0.4 * math.sin(t * 12.56), ring=t * 2.0)
    if animation == "fire":
        return State(glow=1.0, pods=1.0, ring=t * 3.0)
    if animation == "drop":
        u = min(1.0, t / 0.75)
        return State(drop=(1.0 - u) ** 2, glow=0.2 + 0.2 * t, ring=t, sparks=(t - 0.75) / 0.25 if t >= 0.75 else -1.0)
    if animation == "hurt":
        k = [1.0, 0.6, 0.2][min(i, 2)]
        return State(hurt=k, glow=0.2, ring=0.1 * i)
    # death
    burst = min(1.0, t / 0.5)
    return State(glow=max(0.0, 1.0 - t * 3.0), broken=min(1.0, max(0.0, (t - 0.15) / 0.5)), sparks=burst if t < 0.6 else -1.0,
                 smoke=max(0.0, t - 0.2))


def _render_frame(animation: str, frame_index: int, nframes: int) -> Image.Image:
    return draw_uplink(_state_for(animation, frame_index, nframes))


ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": "Command Uplink"},
    "body": {
        "body_plan": "Static",
        "body_kind": "Standard",
        "mass_class": "Heavy",
        "traits": ["machine", "regime"],
        "locomotion_hint": "Stationary",
    },
    "visual": {"default_pose": "idle", "portrait": {"animation": "idle", "frame": 0}},
    "tags": ["regime", "machine"],
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "combat.hurt": {"animation": "hurt", "events": []},
        "combat.death": {"animation": "death", "events": []},
    },
}


def render(out_dir: str | Path, **opts) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=_render_frame,
        out_dir=out_dir,
        frame_size=opts.get("frame_size", FRAME_SIZE),
        auto_crop=False,
        actor_metadata=ACTOR_METADATA,
        animation_key_map={name: name for name, _frames, _duration in ROWS},
    )
    return [outputs[k] for k in ("spritesheet", "yaml", "ron", "actor", "preview", "canonical", "canonical_transparent")]


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
