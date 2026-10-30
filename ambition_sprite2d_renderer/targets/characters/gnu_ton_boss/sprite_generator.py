#!/usr/bin/env python3
"""
GNU-ton boss sprite generator: the sheets of the giant, its fist, and its rider.

GNU-ton is a scholar who stands on the shoulders of a giant GNU. The giant is
drawn by `giant_art` (a giant that is like a gnu and is not one: a beast on
four long legs with a chest that stands up at its front), and the scholar by
`scholar`. This module puts their frames in the sheets the game reads:

  - `giant_gnu`       the giant alone: the MOUNT of the fight
  - `giant_gnu_fist`  one fist alone: each fist is a body of its own
  - `gnu_ton_rider`   the scholar alone: the boss
  - `gnu_ton_boss`    the three together (the Hall's exhibit), and its
                      `_full` / `_body` / `_hands` pages

Rows of the giant's sheets (`ANIMATIONS`): rest, hand_slam, hand_sweep,
head_down, hit, death, buck, stomp. The game reads the first six by index
and pins the last two by name.
"""

from __future__ import annotations

import functools
import math
import shutil
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter

from ambition_sprite2d_renderer.core.manifest_ron import ron_row
from ambition_sprite2d_renderer.registry.pack_groups import policy_for
from ambition_sprite2d_renderer.core.draw import blending_draw
from ambition_sprite2d_renderer.targets.characters.gnu_ton_boss import giant_art as _giant
from ambition_sprite2d_renderer.targets.characters.gnu_ton_boss import scholar as _scholar

RGBA = Tuple[int, int, int, int]

TARGET_NAME = "gnu_ton_boss"
# ADR 0020 mount/rider split (G1): the fused `gnu_ton_boss` giant+scholar sheet
# is additionally emitted as TWO separate actors — the giant wildebeest MOUNT
# (scholar-less) and the scholar RIDER drawn alone/centered. The original
# gnu_ton_boss outputs are UNCHANGED; these are added alongside.
GIANT_TARGET_NAME = "giant_gnu"
RIDER_TARGET_NAME = "gnu_ton_rider"
# One of the giant's two fists, alone, for the fist BODIES the scholar conducts.
# Drawn by the same `draw_hand` as the giant's own sheet (the right fist; the
# left is its mirror), so the fist the player fights IS the giant's fist.
FIST_TARGET_NAME = "giant_gnu_fist"
DATA_DIR = Path(__file__).resolve().parent
# targets/characters/gnu_ton_boss -> the tool checkout root (display paths).
TOOL_ROOT = DATA_DIR.parents[3]

# The frame of the giant's sheets: the frame the giant is drawn in
# (`giant_art.FRAME`). Anchors are in design space: its origin is the middle
# of the frame, +y is down, and one unit is one published pixel.
FRAME_W, FRAME_H = _giant.FRAME
FRAME_SIZE = (FRAME_W, FRAME_H)
SUPERSAMPLE = 2  # the scholar is drawn at 2x and brought down for clean edges

# Origin in design coordinates (center of frame)
OX = FRAME_W // 2
OY = FRAME_H // 2

# Frame counts bumped for smoother in-game animation. Rest cycles a longer
# breathing loop; attack rows interpolate the windup → strike → recover arc
# across more frames so the giant reads as deliberate, not jerky.
ANIMATIONS: List[Tuple[str, int, int]] = [
    ("rest", 10, 110),
    ("hand_slam", 10, 72),
    ("hand_sweep", 10, 65),
    ("head_down", 9, 90),
    ("hit", 6, 80),
    ("death", 10, 105),
    # The gnu's own moves (appended so every row above keeps its index). The
    # conductor pins these by name while the gnu bucks and stomps.
    ("buck", 8, 70),
    ("stomp", 8, 70),
    # The rows of the fight with arms and portals (`giant_art`). Each row above
    # draws the giant with its arms in two portals' lines (the drawing is cut
    # there; the game draws the lines), and its fists are bodies of their own.
    # `armed_*`: the same row with whole arms and the fists on them (phase 1).
    # `armed_rest_b` is a copy of `armed_rest`: a pinned row does not loop, so
    # the game goes from one to the other. `clamp`: the arms go out and into
    # the two lines.
    ("armed_rest", 8, 110),
    ("armed_rest_b", 8, 110),
    ("armed_hit", 5, 80),
    ("armed_buck", 8, 70),
    ("clamp", 8, 80),
    # The blows through a portal's line (`giant_art.BLOWS`), each with the arm
    # (the leg) that throws it: the hammer down, the jab across, the uppercut
    # up; with the left arm the hammer, the hook out behind and the uppercut;
    # `kick_*` the near fore leg with the arms in their lines (after the clamp)
    # and `armed_kick_*` with the arms on. Each windup is 0.72 s (the game
    # plays it over the tell's length, so it ends cocked); each strike, hold
    # and recover is as long as the blow's numbers in `giant_art.BLOWS`, which
    # the game types again. A part frame costs no texels, so the rows are
    # dense: the arm moves by small steps.
    *[(f"{blow}_{part}", frames, ms)
      for blow, rows in (
          ("hammer", ((12, 60), (6, 40), (6, 60), (10, 50))),
          ("jab", ((12, 60), (5, 40), (4, 60), (8, 40))),
          ("upper", ((12, 60), (5, 52), (4, 60), (8, 50))),
          ("left_hammer", ((12, 60), (6, 40), (6, 60), (10, 50))),
          ("left_hook", ((12, 60), (5, 40), (4, 60), (8, 45))),
          ("left_upper", ((12, 60), (5, 52), (4, 60), (8, 50))),
          ("kick", ((12, 60), (5, 60), (4, 60), (6, 70))),
          ("armed_kick", ((12, 60), (5, 60), (4, 60), (6, 70))),
      )
      for part, (frames, ms) in zip(("windup", "strike", "hold", "recover"), rows)],
    # The giant as a character of its own (round 3): it walks (`walk_back`:
    # the same steps backward, its face to the player), looks back at what is
    # on its back, roars, grieves over its fallen rider (its arms hold him),
    # and floats in space with its legs drawn up. `armed_*`: with its arms on.
    ("walk", _giant.WALK_FRAMES, _giant.WALK_MS),
    ("walk_back", _giant.WALK_FRAMES, _giant.WALK_MS),
    ("armed_walk", _giant.WALK_FRAMES, _giant.WALK_MS),
    ("armed_walk_back", _giant.WALK_FRAMES, _giant.WALK_MS),
    ("look_back", 8, 90),
    ("armed_look_back", 8, 90),
    ("roar", 12, 70),
    ("armed_roar", 12, 70),
    ("grieve", 10, 120),
    ("float", 10, 110),
    ("armed_float", 10, 110),
]

# The rows whose giant has its fists on its arms: the fused sheet draws no
# fist beside it.
_ROWS_WITH_FISTS_ON = ("armed_rest", "armed_rest_b", "armed_hit", "armed_buck", "armed_walk", "armed_walk_back",
                       "armed_look_back", "armed_roar", "grieve", "armed_float") + tuple(
    f"{blow}_{part}" for blow in ("hammer", "jab", "upper", "left_hammer", "left_hook", "left_upper", "armed_kick")
    for part in ("windup", "strike", "hold", "recover"))

# Output files: the runtime consumes the split body/hands pair plus the
# canonical SheetRecord RON. Runtime collision/hurtbox metadata is stored in
# the RON's `body_metrics` block, so the old JSON manifest/parts sidecars are
# no longer emitted for GNU-ton.
OUTPUT_FILES = [
    f"{TARGET_NAME}_spritesheet.png",  # alias for _full (back-compat)
    f"{TARGET_NAME}_full_spritesheet.png",
    f"{TARGET_NAME}_body_spritesheet.png",
    f"{TARGET_NAME}_hands_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
    # ADR 0020 split: the giant MOUNT (scholar-less body + shared hands) and the
    # scholar RIDER (drawn alone, its own tight-trim standalone sheet). Emitted
    # into the same `gnu_ton_boss/` install dir alongside the fused sheet.
    f"{GIANT_TARGET_NAME}_spritesheet.png",  # the giant body alone (fists are their own bodies)
    f"{GIANT_TARGET_NAME}_body_spritesheet.png",
    f"{GIANT_TARGET_NAME}_hands_spritesheet.png",
    f"{GIANT_TARGET_NAME}_hands_spritesheet.ron",
    f"{GIANT_TARGET_NAME}_spritesheet.ron",
    f"{GIANT_TARGET_NAME}_actor.ron",
    # The giant drawn from its pieces: the game draws it from these and loads
    # no baked page of it (`_publish_giant_flipbook`). Its part pages after
    # the first (`giant_gnu_parts_1.png`, ...) are installed by name pattern.
    f"{GIANT_TARGET_NAME}_parts.ron",
    f"{GIANT_TARGET_NAME}_parts.png",
    f"{RIDER_TARGET_NAME}_spritesheet.png",
    f"{RIDER_TARGET_NAME}_spritesheet.ron",
    f"{RIDER_TARGET_NAME}_actor.ron",
    f"{FIST_TARGET_NAME}_spritesheet.png",
    f"{FIST_TARGET_NAME}_spritesheet.ron",
    f"{FIST_TARGET_NAME}_actor.ron",
    # This generator does not produce `{TARGET_NAME}_spritesheet_manifest.json`.
    # Any installed copy is an orphaned input, not a declared output.
    # `ambition_ldtk_tools/synth_boss_manifest.py` reads it by name and this
    # renderer's `devtools/ldtk_manifest.py` reads its `frame_size` before
    # falling back to the `.ron` — but the file on disk predates the sheets
    # beside it, so a clean regeneration would not produce it and both readers
    # would silently lose their source. Deleting it is not the fix and neither
    # is declaring it; somebody has to decide whether those readers still need
    # it, and if so what writes it.
]

# Review-only output generated next to the sheets. It is intentionally not in
# OUTPUT_FILES, so `publish` does not install it into the runtime asset tree.
HITBOX_DEBUG_FILE = f"{TARGET_NAME}_hitboxes_debug.png"

ACTOR_METADATA = {
    "authoring_description": (
        "GNU-ton is an Isaac Newton parody mounted on a giant GNU: Newton becomes "
        "GNU-ton through the recursive free-software acronym and a literal horned "
        "wildebeest. Apples, gravity, calculus rivalry, and the absurd mount should all "
        "remain legible parts of the same boss concept."
    ),
    "gameplay_description": (
        "Use as a multipart gravity boss or set-piece encounter. The scholar directs "
        "the giant mount while apples fall, trajectories bend, and separate rider and "
        "mount phases let games split the joke into distinct combat bodies."
    ),
    "dialogue_hints": {
        "barks": [
            "I have discovered gravity. You are demonstrating it.",
            "The apple was evidence, not ammunition. Until now.",
            "GNU-ton is recursively inevitable.",
        ]
    },
    "actor": {"character_id": f"npc_{TARGET_NAME}"},
    "body": {
        "body_plan": "BossMultipart",
        "body_kind": "Wide",
        "traits": ["boss", "multipart"],
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "tags": ["boss", "multipart"],
    "missing_information": [
        "boss schedule/action specials: not authored in the sprite actor contract yet",
    ],
}

# ── ADR 0020 mount/rider actor metadata ──────────────────────────────────────
# The giant GNU is the MOUNT (Mountable): a brainless carried body. The scholar
# is the RIDER (CanPilot). Full wiring (Mountable::rider_offset, two HP pools)
# lands in G2; here we only ship the sprites + a recorded shoulder offset so G2
# can author the rider socket without re-deriving it.
GIANT_ACTOR_METADATA = {
    "authoring_description": (
        "The Giant GNU is the literal wildebeest mount in the GNU-ton Isaac Newton "
        "parody. It carries the visual weight of the recursive GNU pun and should still "
        "read as a formidable horned animal when published without its scholar rider."
    ),
    "gameplay_description": (
        "Use as a mount, independent boss body, charging hazard, or second phase. It is "
        "brainless by design and should communicate through weight, horns, hands, and "
        "gravity-driven movement rather than scholarly dialogue."
    ),
    "dialogue_hints": {"barks": ["GNU.", "The recursion has hooves."]},
    "actor": {"character_id": f"npc_{GIANT_TARGET_NAME}"},
    "body": {
        "body_plan": "BossMultipart",
        "body_kind": "Wide",
        "traits": ["boss", "multipart", "mount"],
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "tags": ["boss", "multipart", "mount"],
    "missing_information": [
        # The catalog authors the seat (`mount.saddle` of `npc_giant_gnu`): the
        # middle of the right shoulder's top, `giant_art.seat_place`.
        "The rider's seat is the catalog's (mount.saddle), from giant_art.seat_place",
    ],
}

RIDER_ACTOR_METADATA = {
    "authoring_description": (
        "The GNU-ton Rider is the Isaac Newton parody separated from his giant GNU "
        "mount. Alone he should read as a severe early-modern scholar whose gravity, "
        "apple, optics, and calculus motifs explain the fused boss's human half."
    ),
    "gameplay_description": (
        "Use as a rider, dismounted boss phase, scholar NPC, or gravity caster. His "
        "standalone sheet lets games give the rider a separate health pool, dialogue, "
        "and precise spell-like control after the mount is lost."
    ),
    "dialogue_hints": {
        "barks": [
            "I have discovered gravity. You are demonstrating it.",
            "The apple was evidence, not ammunition. Until now.",
        ]
    },
    "actor": {"character_id": f"npc_{RIDER_TARGET_NAME}"},
    "body": {
        "body_plan": "Humanoid",
        "body_kind": "Small",
        "traits": ["rider"],
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "tags": ["rider"],
    "missing_information": [
        "CanPilot classes + rider HP pool: authored in G2, not in the sprite "
        "contract",
    ],
}

FIST_ACTOR_METADATA = {
    "authoring_description": (
        "One fist of the Giant GNU, alone: the hoof-knuckled hand GNU-ton conducts "
        "like a lecturer's pointer. It is the giant's own hand art, so the fist the "
        "player dodges is the fist drawn on the giant."
    ),
    "gameplay_description": (
        "A floating limb body the GNU-ton rider drives: it slams, swings on a "
        "pendulum, traces curves and orbits the giant. Striking it hurts the "
        "scholar who conducts it."
    ),
    "dialogue_hints": {"barks": ["*knuckles crack*", "Talk to the hoof."]},
    "actor": {"character_id": f"npc_{FIST_TARGET_NAME}"},
    "body": {
        "body_plan": "BossMultipart",
        "body_kind": "Wide",
        "traits": ["boss", "limb"],
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "tags": ["limb", "giant"],
    "missing_information": [],
}

# ── Palette ──────────────────────────────────────────────────────────────────
# Powdered wig (Isaac Newton style): cream-white with a soft warm shadow
# so the curls read against the dark wildebeest mane behind the scholar.
C_SPEECH_BG = (248, 246, 238, 220)
C_SPEECH_EDGE = (180, 170, 148, 255)
C_SPEECH_TXT = (28, 22, 14, 255)
C_BG = (0, 0, 0, 0)  # transparent background


def wave(phase: float, freq: float = 1.0, offset: float = 0.0) -> float:
    return math.sin(math.tau * (phase * freq + offset))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def smoothstep(t: float) -> float:
    t = clamp(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


class Canvas:
    """Drawing helper with design-space coordinates (origin at frame center)."""

    def __init__(self, w: int, h: int, bg: RGBA = C_BG, scale: int = 1):
        self.scale = scale
        self.sw = w * scale
        self.sh = h * scale
        self.img = Image.new("RGBA", (self.sw, self.sh), bg)
        self.draw = blending_draw(self.img)
        # Origin in scaled pixel space
        self.ox = (w // 2) * scale
        self.oy = (h // 2) * scale

    def P(self, x: float, y: float) -> Tuple[int, int]:
        """Design-space point -> pixel coordinate."""
        return (
            int(round(self.ox + x * self.scale)),
            int(round(self.oy + y * self.scale)),
        )

    def Ps(self, pts):
        return [self.P(x, y) for x, y in pts]

    def polygon(
        self, pts, fill: RGBA, outline: Optional[RGBA] = None, width: float = 1.5
    ):
        px = self.Ps(pts)
        self.draw.polygon(px, fill=fill)
        if outline:
            self.draw.line(
                px + [px[0]],
                fill=outline,
                width=max(1, int(round(width * self.scale))),
                joint="curve",
            )

    def ellipse(
        self,
        cx: float,
        cy: float,
        rx: float,
        ry: float,
        fill: RGBA,
        outline: Optional[RGBA] = None,
        width: float = 1.5,
    ):
        p0 = self.P(cx - rx, cy - ry)
        p1 = self.P(cx + rx, cy + ry)
        self.draw.ellipse(
            [p0, p1],
            fill=fill,
            outline=outline,
            width=max(1, int(round(width * self.scale))),
        )

    def alpha_ellipse(
        self,
        cx: float,
        cy: float,
        rx: float,
        ry: float,
        fill: RGBA,
        blur: float = 0.0,
        outline: Optional[RGBA] = None,
        width: float = 1.5,
    ):
        """Draw a translucent ellipse using real alpha compositing."""
        layer = Image.new("RGBA", (self.sw, self.sh), (0, 0, 0, 0))
        d = blending_draw(layer)

        p0 = self.P(cx - rx, cy - ry)
        p1 = self.P(cx + rx, cy + ry)

        d.ellipse([p0, p1], fill=fill)

        if outline:
            d.ellipse(
                [p0, p1],
                outline=outline,
                width=max(1, int(round(width * self.scale))),
            )

        if blur > 0:
            layer = layer.filter(
                ImageFilter.GaussianBlur(max(1, int(round(blur * self.scale))))
            )

        self.img = Image.alpha_composite(self.img, layer)
        self.draw = blending_draw(self.img)

    def line(self, pts, fill: RGBA, width: float = 2.0):
        px = self.Ps(pts)
        self.draw.line(
            px, fill=fill, width=max(1, int(round(width * self.scale))), joint="curve"
        )

    def arc_pts(
        self,
        cx: float,
        cy: float,
        rx: float,
        ry: float,
        start_deg: float,
        end_deg: float,
        n: int = 20,
    ) -> list:
        pts = []
        for i in range(n + 1):
            t = i / n
            a = math.radians(lerp(start_deg, end_deg, t))
            pts.append((cx + math.cos(a) * rx, cy + math.sin(a) * ry))
        return pts

    def finish(self) -> Image.Image:
        if self.scale > 1:
            return self.img.resize(
                (self.sw // self.scale, self.sh // self.scale), Image.LANCZOS
            )
        return self.img


# ── Drawing primitives ───────────────────────────────────────────────────────


# The fused sheet's rows, drawn with the scholar's own rows.
_FUSED_SCHOLAR_ROW = {
    "rest": "rest",
    "hand_slam": "point",
    "hand_sweep": "conduct",
    "head_down": "invoke",
    "hit": "hit",
    "death": "death",
    "buck": "brace",
    "stomp": "point",
    "armed_rest": "rest",
    "armed_rest_b": "rest",
    "armed_hit": "hit",
    "armed_buck": "brace",
    "clamp": "invoke",
    **{f"{blow}_{part}": ("conduct" if part == "recover" else "point")
       for blow in ("hammer", "jab", "upper", "left_hammer", "left_hook", "left_upper", "kick", "armed_kick")
       for part in ("windup", "strike", "hold", "recover")},
}
# On the giant he is drawn at this multiple of his design size, so he stands as
# tall as the figure he replaced (~45 design px, sole to wig).
_FUSED_SCHOLAR_SCALE = 1.35
# The old figure's soles sat this far below the `hy` it was handed.
_OLD_SOLE_BELOW_HY = 17.0


def draw_gnu_ton_man(
    c: Canvas,
    hx: float = 0.0,
    hy: float = 0.0,
    phase: float = 0.0,
    anim: str = "rest",
    show_speech: bool = False,
) -> None:
    """The GNU-ton scholar standing atop the GNU's neck/back.

    Drawn by `scholar.draw_scholar` (v2: three-quarter view, long coat, powdered
    wig with queue, quill and Principia), the same figure his own rider sheet
    uses, so the Hall portrait and the fight show one man. `hy` keeps its old
    meaning — his soles are `_OLD_SOLE_BELOW_HY` below it.
    """
    row = _FUSED_SCHOLAR_ROW.get(anim, "rest")
    frames = _scholar.row_frames(row)
    frame = min(frames - 1, int(phase * frames))
    pelvis_y = hy + _OLD_SOLE_BELOW_HY - _scholar.PELVIS_TO_SOLE * _FUSED_SCHOLAR_SCALE
    _scholar.draw_scholar(c, hx, pelvis_y, _scholar.pose_for(row, frame, frames), scale=_FUSED_SCHOLAR_SCALE)

    # Speech bubble (kept for canonical / debug renders; in-game uses the
    # bark system instead).
    if show_speech:
        bx = hx + 14
        by = hy - 34
        bw, bh = 60, 24
        c.polygon(
            [
                (bx, by),
                (bx + bw, by),
                (bx + bw, by + bh),
                (bx + 6, by + bh),
                (bx + 2, by + bh + 8),
                (bx + 12, by + bh),
                (bx, by + bh),
            ],
            C_SPEECH_BG,
            C_SPEECH_EDGE,
            1.0,
        )
        for x0, y0, x1, y1 in [
            (bx + 5, by + 6, bx + 44, by + 6),
            (bx + 5, by + 12, bx + 50, by + 12),
            (bx + 5, by + 18, bx + 34, by + 18),
        ]:
            c.line([(x0, y0), (x1, y1)], C_SPEECH_TXT, 1.2)


# ── Per-animation frame drawing ──────────────────────────────────────────────


# Where each fist is in the fused sheet's frame at rest: beside the giant, at
# the height of its chest. (The fists the player fights are bodies of their
# own, from `giant_gnu_fist`; these are the picture of the Hall's exhibit.)
# Not farther out than this: the widest frame of the pack says how wide each
# cell of its pages is, and ten cells must be under 8192 px.
_FUSED_FIST_X = 295.0
_FUSED_FIST_Y = 330.0
_FUSED_FIST_FLOOR_Y = 606.0
# The scholar on the giant's shoulder in the fused sheet: his own rider frame,
# at the size he has beside the giant in the fight (85 px of body).
_RIDER_REST_BBOX = (65, 31, 69, 126)
_FUSED_SCHOLAR_BODY_PX = 85.0


@functools.lru_cache(maxsize=None)
def _giant_frame(anim: str, frame_idx: int, frame_count: int) -> Image.Image:
    """The giant's frame for the layers of the sheets (each layer draws it):
    composed once. The part flipbook records its own render of each frame
    (`_publish_giant_flipbook`): a cached frame carries no record."""
    return _giant.render_giant(anim, frame_idx, frame_count)


#: Where the giant's feet are in its frame: the middle of the floor line. The
#: part flipbook places each draw from here.
GIANT_FEET = (FRAME_W * 0.5, float(_giant.to_frame((0.0, _giant.FLOOR))[1]))


def _publish_giant_flipbook(outdir: Path, sheet_page: Image.Image) -> List[Path]:
    """The giant's part flipbook (`giant_gnu_parts.ron` and its pages), beside
    its sheet. The giant is drawn from pieces (`giant_art.scene_for`), so the
    flipbook keeps each piece once and where it is in each frame: the game
    draws the giant from it and loads no baked page. Its road is the measured
    one: parts unless their pages hold more texels than the sheet, or a frame
    takes more draws than the most a part-drawn body may."""
    from ambition_sprite2d_renderer.authoring.part_flipbook import (
        REALIZE_BAKED, REALIZE_MAX_DRAWS, REALIZE_PARTS, build_rig_flipbook)
    from ambition_sprite2d_renderer.authoring.sheet_build import rendering_quality_tier

    if rendering_quality_tier():
        return []
    flipbook = build_rig_flipbook(GIANT_TARGET_NAME, ANIMATIONS, _giant.render_giant, None, GIANT_FEET, FRAME_SIZE)
    flipbook.pack()
    most = max(len(draws) for _d, frames in flipbook.clips.values() for draws in frames)
    sheet_texels = sheet_page.width * sheet_page.height
    cheaper = flipbook.packed_texels() <= sheet_texels and most <= REALIZE_MAX_DRAWS
    flipbook.realize = REALIZE_PARTS if cheaper else REALIZE_BAKED
    print(f"  [part flipbook] {GIANT_TARGET_NAME}: realize {flipbook.realize} (part pages {flipbook.packed_texels()} "
          f"texels, sheet {sheet_texels}; at most {most} draws a frame)", flush=True)
    return list(flipbook.write(outdir).values())


@functools.lru_cache(maxsize=None)
def _fist_rest() -> Image.Image:
    return _giant.render_fist("rest", 0, 10)


def _fused_fists(anim: str, phase: float) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """Where the left and the right fist are in the frame (their middles)."""
    cx = FRAME_W * 0.5
    bob = 4.0 * math.sin(2.0 * math.pi * phase)
    x, y = _FUSED_FIST_X, _FUSED_FIST_Y + bob
    if anim == "hand_slam":
        up = math.sin(math.pi * min(1.0, phase / 0.45)) if phase < 0.45 else 0.0
        down = min(1.0, (phase - 0.45) / 0.12) if phase >= 0.45 else 0.0
        back = max(0.0, (phase - 0.8) / 0.2)
        y = _FUSED_FIST_Y - 70.0 * up + (_FUSED_FIST_FLOOR_Y - _FUSED_FIST_Y) * down * (1.0 - back)
    elif anim == "hand_sweep":
        sweep = math.sin(math.pi * phase)
        x = _FUSED_FIST_X - 150.0 * sweep
        y = _FUSED_FIST_Y + (_FUSED_FIST_FLOOR_Y - 30.0 - _FUSED_FIST_Y) * sweep
    elif anim == "death":
        y = _FUSED_FIST_Y + (_FUSED_FIST_FLOOR_Y - _FUSED_FIST_Y) * smoothstep(clamp((phase - 0.2) / 0.5, 0.0, 1.0))
    return (cx - x, y), (cx + x, y)


def draw_frame(
    anim: str,
    frame_idx: int,
    frame_count: int,
    layer: str = "full",
    parts: Optional[dict] = None,
) -> Image.Image:
    """Render one animation frame and return a FRAME_SIZE RGBA image.

    `layer` selects what is in it:
      - "full"       : the giant, the scholar on its shoulder, the two fists
      - "body"       : the giant and the scholar
      - "hands"      : the two fists
      - "giant_body" : the giant alone (the MOUNT of the fight)
      - "scholar"    : the scholar alone, in the middle of the frame
    `parts` collects design-space anchor positions for runtime hitboxes.
    Pass the same dict across all frames of a row to accumulate the row.
    """
    phase = frame_idx / max(1, frame_count)
    if layer == _SCHOLAR_LAYER:
        c = Canvas(FRAME_W, FRAME_H, C_BG, scale=SUPERSAMPLE)
        draw_gnu_ton_man(c, 0.0, _RIDER_CENTER_Y, phase=phase, anim=anim, show_speech=False)
        return c.finish()

    pose = _giant.pose_for(anim, phase)
    frame = Image.new("RGBA", FRAME_SIZE, (0, 0, 0, 0))
    if layer in ("full", "body", _GIANT_BODY_LAYER):
        frame.alpha_composite(_giant_frame(anim, frame_idx, frame_count))

    seat = _giant.seat_place(pose)
    scale = _FUSED_SCHOLAR_BODY_PX / _RIDER_REST_BBOX[3]
    if layer in ("full", "body"):
        row = _FUSED_SCHOLAR_ROW.get(anim, "rest")
        frames = _scholar.row_frames(row)
        man = _scholar.render_frame(
            Canvas, row, min(frames - 1, int(phase * frames)), frames, RIDER_FRAME, RIDER_PX_PER_UNIT, SUPERSAMPLE
        )
        man = man.resize((round(man.width * scale), round(man.height * scale)), Image.LANCZOS)
        bx, by, bw, bh = _RIDER_REST_BBOX
        frame.alpha_composite(
            man, (round(seat[0] - (bx + bw * 0.5) * scale), round(seat[1] - (by + bh) * scale))
        )

    left, right = _fused_fists(anim, phase)
    if layer in ("full", "hands") and anim not in _ROWS_WITH_FISTS_ON:
        fist = _fist_rest()
        bx, by, bw, bh = _giant.FIST_BBOX
        for (x, y), image, cx in (
            (right, fist, bx + bw * 0.5),
            (left, fist.transpose(Image.FLIP_LEFT_RIGHT), fist.width - (bx + bw * 0.5)),
        ):
            frame.alpha_composite(image, (round(x - cx), round(y - (by + bh * 0.5))))

    head = _giant.head_place(pose)
    _record_parts(
        parts,
        anim,
        frame_idx,
        head=(head[0] - OX, head[1] - OY),
        hand_left=(left[0] - OX, left[1] - OY),
        hand_right=(right[0] - OX, right[1] - OY),
        scholar=(seat[0] - OX, seat[1] - _FUSED_SCHOLAR_BODY_PX * 0.5 - OY),
    )
    return frame


# Where the giant's parts are at rest, in design space (the origin is the
# middle of the frame, +y is down): what the fused sheet's boxes fall back to
# when a row recorded no anchor.
REST_HEAD_X = 110.0
REST_HEAD_Y = -108.0
REST_HAND_X = _FUSED_FIST_X
REST_HAND_Y = _FUSED_FIST_Y - FRAME_H * 0.5
# How deep a fist of the fused sheet goes in its slam: to the floor.
SLAM_STRIKE_Y = _FUSED_FIST_FLOOR_Y - FRAME_H * 0.5

# ADR 0020 RIDER split: the standalone scholar frame draws the man CENTERED at
# man_x=0. The scholar figure spans design-y ≈ (hy-24) wig top .. (hy+19) feet;
# its midpoint is hy-2.5, so hy=2.5 centers that span on the frame center. The
# rider sheet is packed on its OWN tight trim, so this only sets the (cosmetic)
# frame-relative centering — the runtime addresses the trimmed rect + off.
_RIDER_CENTER_Y = 2.5
# The rider's published frame: a tight window around the frame centre, where
# `draw_frame(layer="scholar")` draws him. Published at 768x576 the scholar was
# 39x52 pixels of a frame the runtime scaled to his collision box, so he drew
# at a sixth of his size. The window keeps every row's pose (the widest, his
# death fall, spans x 361..410 / y 261..316).
# v2: his own frame, drawn directly (not cropped from the giant's canvas) at
# `RIDER_PX_PER_UNIT` pixels per design unit. The runtime draws the frame at
# `basis x collision_scale` world units tall whatever its pixel size, so twice
# the pixels is twice the detail at the same world size (0.875 wu/px).
RIDER_FRAME = (192, 192)
RIDER_PX_PER_UNIT = 3
# His rows, in the order the boss sheet's fixed slots read them (see
# `scholar.SLOT_ROWS`), then the named rows a move or the conductor asks for.
RIDER_ROWS = [(name, frames, int(round(secs * 1000))) for name, frames, secs in _scholar.ROWS]


def _record_parts(
    parts: Optional[dict],
    anim: str,
    frame_idx: int,
    head: Tuple[float, float],
    hand_left: Tuple[float, float],
    hand_right: Tuple[float, float],
    scholar: Tuple[float, float],
    extra: Optional[dict] = None,
) -> None:
    """Append one frame's design-space anchors into the parts dict.

    Consumed by the runtime to position hitboxes against the actually-drawn
    parts rather than guessing at fixed offsets.
    """
    if parts is None:
        return
    entry = {
        "frame": frame_idx,
        "head": [round(head[0], 2), round(head[1], 2)],
        "hand_left": [round(hand_left[0], 2), round(hand_left[1], 2)],
        "hand_right": [round(hand_right[0], 2), round(hand_right[1], 2)],
        "scholar": [round(scholar[0], 2), round(scholar[1], 2)],
    }
    if extra:
        entry.update(extra)
    parts.setdefault(anim, []).append(entry)


# ── Runtime RON manifest ────────────────────────────────────────────────────

_HEAD_BOX_W = 112
_HEAD_BOX_H = 150
_HAND_BOX_W = 104
_HAND_BOX_H = 84
# GNU-ton's damageable head hurtbox is intentionally a little tighter
# than the dangerous head hitbox. Keeping both boxes centered on the
# same anchor makes the debug preview readable (cyan inside red) and
# gives gameplay a small forgiving margin near the visual edge.
_HEAD_HURTBOX_SCALE = 0.90


def _pixel_rect_from_center(cx: float, cy: float, w: int, h: int) -> dict:
    return {
        "x": int(round(OX + cx - w * 0.5)),
        "y": int(round(OY + cy - h * 0.5)),
        "w": int(w),
        "h": int(h),
    }


def _part_rect(name: str, rect: dict) -> dict:
    out = {"name": name}
    out.update(rect)
    return out


def _head_rect(head_anchor) -> dict:
    x, y = head_anchor
    return _part_rect(
        "head", _pixel_rect_from_center(float(x), float(y), _HEAD_BOX_W, _HEAD_BOX_H)
    )


def _scale_part_rect_centered(part: dict, scale: float) -> dict:
    """Scale a generated pixel rect around its current center."""
    out = dict(part)
    scale = clamp(float(scale), 0.0, 1.0)
    cx = float(part["x"]) + float(part["w"]) * 0.5
    cy = float(part["y"]) + float(part["h"]) * 0.5
    w = max(1, int(round(float(part["w"]) * scale)))
    h = max(1, int(round(float(part["h"]) * scale)))
    out["x"] = int(round(cx - w * 0.5))
    out["y"] = int(round(cy - h * 0.5))
    out["w"] = w
    out["h"] = h
    return out


def _head_hurt_rect(head_anchor) -> dict:
    return _scale_part_rect_centered(_head_rect(head_anchor), _HEAD_HURTBOX_SCALE)


def _ron_part(part: dict) -> str:
    return (
        f'(name: "{part["name"]}", x: {part["x"]}, y: {part["y"]}, '
        f"w: {part['w']}, h: {part['h']})"
    )


def _ron_part_list(parts: list[dict]) -> str:
    if not parts:
        return "[]"
    return "[" + ", ".join(_ron_part(p) for p in parts) + "]"


def _ron_box(box: dict) -> str:
    fields = [f"parts: {_ron_part_list(box.get('parts', []))}"]
    frames = box.get("frames")
    if frames:
        frame_items = [
            f"(parts: {_ron_part_list(frame_box.get('parts', []))})"
            for frame_box in frames
        ]
        fields.append("frames: [" + ", ".join(frame_items) + "]")
    return "(" + ", ".join(fields) + ")"


def _ron_anim_entry(entry: dict) -> str:
    fields = []
    frame_duration_secs = entry.get("frame_duration_secs")
    if frame_duration_secs is not None:
        fields.append(f"frame_duration_secs: Some({float(frame_duration_secs):.6g})")
    hurtbox = entry.get("hurtbox")
    hitbox = entry.get("hitbox")
    if hurtbox is not None:
        fields.append(f"hurtbox: Some({_ron_box(hurtbox)})")
    if hitbox is not None:
        fields.append(f"hitbox: Some({_ron_box(hitbox)})")
    return "(" + ", ".join(fields) + ")"


def _box(parts: list[dict], frames: list[dict] | None = None) -> dict:
    out = {"parts": parts}
    if frames:
        out["frames"] = frames
    return out


def _animation_duration_secs(anim: str) -> float:
    for name, _frame_count, duration_ms in ANIMATIONS:
        if name == anim:
            return float(duration_ms) / 1000.0
    raise KeyError(anim)


def _head_hurt_frames(parts_doc: dict, anim: str) -> list[dict]:
    return [
        {"parts": [_head_hurt_rect(frame["head"])]}
        for frame in parts_doc["anchors"].get(anim, [])
    ]


def _head_hit_frames(parts_doc: dict, anim: str) -> list[dict]:
    return [
        {"parts": [_head_rect(frame["head"])]}
        for frame in parts_doc["anchors"].get(anim, [])
    ]


def _hand_hit_frames(parts_doc: dict, anim: str) -> list[dict]:
    frames = []
    for frame in parts_doc["anchors"].get(anim, []):
        left_x, left_y = frame["hand_left"]
        right_x, right_y = frame["hand_right"]
        frames.append(
            {
                "parts": [
                    _part_rect(
                        "left_hand",
                        _pixel_rect_from_center(
                            float(left_x), float(left_y), _HAND_BOX_W, _HAND_BOX_H
                        ),
                    ),
                    _part_rect(
                        "right_hand",
                        _pixel_rect_from_center(
                            float(right_x), float(right_y), _HAND_BOX_W, _HAND_BOX_H
                        ),
                    ),
                ]
            }
        )
    return frames


def _first_part(frames: list[dict], fallback: dict) -> dict:
    for frame in frames:
        parts = frame.get("parts", [])
        if parts:
            return parts[0]
    return fallback


def _deepest_frame_parts(frames: list[dict], fallback: list[dict]) -> list[dict]:
    if not frames:
        return list(fallback)
    return list(
        max(
            frames,
            key=lambda frame: max(
                (part["y"] for part in frame.get("parts", [])), default=-10_000
            ),
        ).get("parts", fallback)
    )


def _widest_frame_parts(frames: list[dict], fallback: list[dict]) -> list[dict]:
    if not frames:
        return list(fallback)
    return list(
        max(
            frames,
            key=lambda frame: max(
                (
                    abs(part["x"] + part["w"] * 0.5 - OX)
                    for part in frame.get("parts", [])
                ),
                default=-1.0,
            ),
        ).get("parts", fallback)
    )


def _row_hurt_entry(parts_doc: dict, anim: str) -> dict:
    frames = _head_hurt_frames(parts_doc, anim)
    fallback = _head_hurt_rect((REST_HEAD_X, REST_HEAD_Y))
    entry = {
        "frame_duration_secs": _animation_duration_secs(anim),
        "hurtbox": _box([_first_part(frames, fallback)], frames),
    }
    return {k: v for k, v in entry.items() if v is not None}


def _row_head_hit_entry(parts_doc: dict, anim: str) -> dict:
    hurt_frames = _head_hurt_frames(parts_doc, anim)
    hit_frames = _head_hit_frames(parts_doc, anim)
    hurt_fallback = _head_hurt_rect((REST_HEAD_X, REST_HEAD_Y))
    hit_fallback = _head_rect((REST_HEAD_X, REST_HEAD_Y))
    hurt_parts = _deepest_frame_parts(hurt_frames, [hurt_fallback])
    hit_parts = _deepest_frame_parts(hit_frames, [hit_fallback])
    entry = {
        "frame_duration_secs": _animation_duration_secs(anim),
        "hurtbox": _box(hurt_parts, hurt_frames),
        "hitbox": _box(hit_parts, hit_frames),
    }
    return {k: v for k, v in entry.items() if v is not None}


def _gnu_ton_body_metrics(parts_doc: dict) -> dict:
    """Return the exact per-animation metrics emitted into the runtime RON.

    The hitbox debug preview also consumes this data, keeping the visual
    review path tied to the same rectangles the Rust runtime loads. Every
    moving gameplay box is derived from anchors recorded while drawing the
    frames; no gameplay-only coordinates should be invented here.
    """
    rest_hurt = _row_hurt_entry(parts_doc, "rest")
    hit_hurt = _row_hurt_entry(parts_doc, "hit")
    hand_slam_hurt = _row_hurt_entry(parts_doc, "hand_slam")
    hand_sweep_hurt = _row_hurt_entry(parts_doc, "hand_sweep")
    head_down_boxes = _row_head_hit_entry(parts_doc, "head_down")

    hand_slam_frames = _hand_hit_frames(parts_doc, "hand_slam")
    hand_sweep_frames = _hand_hit_frames(parts_doc, "hand_sweep")
    hand_slam_fallback = [
        _part_rect(
            "left_hand",
            _pixel_rect_from_center(
                -REST_HAND_X, SLAM_STRIKE_Y, _HAND_BOX_W, _HAND_BOX_H
            ),
        ),
        _part_rect(
            "right_hand",
            _pixel_rect_from_center(
                REST_HAND_X, SLAM_STRIKE_Y, _HAND_BOX_W, _HAND_BOX_H
            ),
        ),
    ]
    hand_sweep_fallback = [
        _part_rect(
            "left_hand",
            _pixel_rect_from_center(
                -REST_HAND_X, REST_HAND_Y, _HAND_BOX_W, _HAND_BOX_H
            ),
        ),
        _part_rect(
            "right_hand",
            _pixel_rect_from_center(REST_HAND_X, REST_HAND_Y, _HAND_BOX_W, _HAND_BOX_H),
        ),
    ]
    shockwave = _part_rect("shockwave", {"x": FRAME_W // 2 - 300, "y": FRAME_H - 44, "w": 600, "h": 36})

    gnu_hand_slam = dict(hand_slam_hurt)
    gnu_hand_slam["hitbox"] = _box(
        _deepest_frame_parts(hand_slam_frames, hand_slam_fallback),
        hand_slam_frames,
    )
    gnu_shockwave = dict(hand_slam_hurt)
    gnu_shockwave["hitbox"] = _box([shockwave])
    gnu_hand_sweep = dict(hand_sweep_hurt)
    gnu_hand_sweep["hitbox"] = _box(
        _widest_frame_parts(hand_sweep_frames, hand_sweep_fallback),
        hand_sweep_frames,
    )

    return {
        # Visual-row keys. The runtime's live animation sample uses these so
        # damageable hurtboxes follow the exact row/frame being rendered.
        "rest": rest_hurt,
        "hand_slam": hand_slam_hurt,
        "hand_sweep": hand_sweep_hurt,
        "head_down": head_down_boxes,
        "hit": hit_hurt,
        # Profile-specific keys. Dangerous attack hitboxes still use these so
        # multiple gameplay profiles can share one visual row without losing
        # their distinct damage volumes.
        "gnu_hand_slam": gnu_hand_slam,
        "gnu_shockwave": gnu_shockwave,
        "gnu_hand_sweep": gnu_hand_sweep,
        "gnu_head_descent": head_down_boxes,
    }


def _gnu_ton_body_metrics_ron(parts_doc: dict) -> str:
    animations = _gnu_ton_body_metrics(parts_doc)
    lines = ["        body_metrics: Some((", "            animations: {"]
    for name, body in animations.items():
        lines.append(f'                "{name}": {_ron_anim_entry(body)},')
    lines.extend(["            },", "        )),"])
    return "\n".join(lines)


def _authored_body_metrics_ron(bbox: Tuple[int, int, int, int]) -> str:
    """A `body_metrics` block that states one authored gameplay body.

    `bbox` is `(x, y, w, h)` in frame pixels. `authored_body: true` is what lets
    a character say "my body is my art" (`with_sprite_authored_body`): the
    runtime sizes the collision box from this rectangle and puts the art on it.
    """
    x, y, w, h = bbox
    return (
        "        body_metrics: Some((\n"
        f"            body_pixel_bbox: Some((x: {x}, y: {y}, w: {w}, h: {h})),\n"
        "            authored_body: true,\n"
        "        )),"
    )


def _union_bbox(images) -> Tuple[int, int, int, int]:
    """The union alpha-bbox of `images`, as `(x, y, w, h)`."""
    boxes = [im.getbbox() for im in images]
    boxes = [b for b in boxes if b]
    x0 = min(b[0] for b in boxes)
    y0 = min(b[1] for b in boxes)
    x1 = max(b[2] for b in boxes)
    y1 = max(b[3] for b in boxes)
    return (x0, y0, x1 - x0, y1 - y0)


def _giant_seams(anim: str, frame_idx: int, frame_count: int) -> dict:
    """Where the giant's arms are cut at their lines in a frame (as
    `giant_art.render_giant` poses it)."""
    return _giant.limb_seams(_giant.pose_for(anim, frame_idx / max(1, frame_count)))


def _with_seam_anchors(rows_meta: list[dict], seams_of, frame_size, surfaces_of=None) -> list[dict]:
    """``rows_meta`` with the seams of each frame as its anchors
    (`giant_art.limb_seam_anchors`): ``seams_of(row, frame, count)``; and,
    with ``surfaces_of(row, frame, count)``, its standing surfaces
    (`giant_art.surface_anchors`)."""
    out = []
    for row in rows_meta:
        count = row["frame_count"]
        rects = []
        for f, rect in enumerate(row["rects"]):
            anchors = _giant.limb_seam_anchors(seams_of(row["animation"], f, count), frame_size)
            if surfaces_of is not None:
                anchors.update(_giant.surface_anchors(surfaces_of(row["animation"], f, count), frame_size))
            rects.append(dict(rect, anchors=anchors) if anchors else rect)
        out.append(dict(row, rects=rects))
    return out


def _giant_surfaces(anim: str, frame_idx: int, frame_count: int) -> dict:
    """Where the giant's standing surfaces are in a frame (as
    `giant_art.render_giant` poses it)."""
    return _giant.surfaces(_giant.pose_for(anim, frame_idx / max(1, frame_count)))


def _runtime_spritesheet_ron(
    rows_meta: list[dict],
    parts_doc: dict,
    images: list[str],
    *,
    target: str = TARGET_NAME,
    include_metrics: bool = True,
    frame_size: Tuple[int, int] = FRAME_SIZE,
    metrics_ron: Optional[str] = None,
) -> str:
    """Compose the `Vec<SheetRecord>` RON.

    The frame addressing (explicit rects + per-frame `page`/`off` trim) goes
    through the SHARED [`ron_row`] writer — the same packed-rect algebra every
    other sheet uses. Only the `body_metrics` block stays bespoke: GNU-ton ships
    a richer per-frame multipart hurt/hit schema than the generic writer models,
    so its emitter ([`_gnu_ton_body_metrics_ron`]) is kept verbatim.

    `target` names both the SheetRecord `target` and its `<target>_spritesheet.png`
    image (the giant MOUNT and scholar RIDER reuse this writer). `include_metrics`
    gates the giant's per-frame hurt/hit schema: the giant MOUNT keeps it (same
    body), the scholar RIDER omits it (it carries none of the giant's parts)."""
    if metrics_ron is not None:
        metrics = f"{metrics_ron}\n"
    elif include_metrics:
        metrics = f"{_gnu_ton_body_metrics_ron(parts_doc)}\n"
    else:
        metrics = ""
    rows_inner = "\n    ".join(ron_row(r) + "," for r in rows_meta)
    images_field = ""
    if len(images) > 1:
        joined = ", ".join(f'"{name}"' for name in images)
        images_field = f"    images: [{joined}],\n"
    return (
        "[\n"
        "(\n"
        f'    target: "{target}",\n'
        f'    image: "{target}_spritesheet.png",\n'
        f"{images_field}"
        "    label_width: 0,\n"
        f"    frame_width: {frame_size[0]},\n"
        f"    frame_height: {frame_size[1]},\n"
        f"{metrics}"
        f"    rows: [\n    {rows_inner}\n    ],\n"
        "    tuning: None,\n"
        "),\n"
        "]\n"
    )


# ── Sheet assembly ───────────────────────────────────────────────────────────

# Layers PUBLISHED as the fused `gnu_ton_boss` sheet (unchanged).
_LAYERS = ("full", "body", "hands")

# ADR 0020 split layers. `giant_body` = the giant body WITHOUT the scholar
# (`_draw_body_layer(draw_man=False)`), lockstep-packed with full/body/hands so
# it shares the same per-frame placement (its alpha is a subset of `full`).
# `scholar` = the scholar drawn ALONE + centered, packed on its OWN tight trim.
_GIANT_BODY_LAYER = "giant_body"
_SCHOLAR_LAYER = "scholar"
# All layers that lockstep-pack onto the shared `full` placement.
_LOCKSTEP_LAYERS = ("full", "body", "hands", _GIANT_BODY_LAYER)


def _pack_layers(rendered: dict, manifest_rows: list[dict], policy, layers=_LAYERS):
    """Lockstep-pack the full/body/hands layers onto ONE page each.

    GNU-ton's three layers must share an IDENTICAL per-frame layout: the runtime
    z-layers the body behind platforms and the hands in front, mirroring the
    body's flat index + trim onto the hands child. So we pack the FULL layer
    (whose alpha is the union of body+hands) once and reuse that placement for
    all three, cropping each layer to the FULL frame's trim bbox. The single
    published record then drives all three textures.

    Returns ``(layer_pages, rows_meta, num_pages)`` where ``layer_pages`` maps
    each layer name to its list of page images (single page)."""
    from ambition_sprite2d_renderer.authoring.packer import FrameInput, pack_frames

    frames = [
        FrameInput(
            key=(r["row"], f),
            image=rendered["full"][(r["row"], f)],
            logical_size=(FRAME_W, FRAME_H),
        )
        for r in manifest_rows
        for f in range(r["frames"])
    ]
    # `policy.page_size` is set large for gnu_ton (registry/pack_groups.py) so
    # the binary-search single-bin packer keeps all frames on ONE page — the
    # split-layer record carries one image per layer, so multi-page siblings
    # (which would resolve the wrong layer's page filename) are not supported.
    result = pack_frames(
        frames,
        max_dim=policy.max_dim,
        page_size=policy.page_size,
        padding=1,
        trim=policy.trim,
    )
    if len(result.pages) != 1:
        raise ValueError(
            f"{TARGET_NAME}: lockstep split-layer pack must fit ONE page, got "
            f"{len(result.pages)} — raise the gnu_ton page_size policy"
        )

    layer_pages: dict[str, list[Image.Image]] = {}
    page_size = result.pages[0].size
    from ambition_sprite2d_renderer.core.memory_budget import require_images

    require_images([page_size] * (len(layers) - 1), f"{TARGET_NAME} layer pages")
    for layer in layers:
        if layer == "full":
            layer_pages[layer] = list(result.pages)
            continue
        page = Image.new("RGBA", page_size, (0, 0, 0, 0))
        for (row, f), pl in result.placements.items():
            crop = rendered[layer][(row, f)].crop(
                (pl.off_x, pl.off_y, pl.off_x + pl.w, pl.off_y + pl.h)
            )
            page.alpha_composite(crop, (pl.x, pl.y))
        layer_pages[layer] = [page]

    rows_meta = []
    for r in manifest_rows:
        rects = []
        for f in range(r["frames"]):
            pl = result.placements[(r["row"], f)]
            rect = {"x": pl.x, "y": pl.y, "w": pl.w, "h": pl.h, "fpage": pl.page}
            if pl.off_x or pl.off_y:
                rect["off"] = (pl.off_x, pl.off_y)
            rects.append(rect)
        dur = r["duration_ms"]
        rows_meta.append(
            {
                "animation": r["name"],
                "row_index": r["row"],
                "frame_count": r["frames"],
                "duration_ms": dur,
                "duration_secs": round(dur / 1000.0, 6),
                "page": result.placements[(r["row"], 0)].page if r["frames"] else 0,
                "rects": rects,
            }
        )
    return layer_pages, rows_meta, len(result.pages)


def _pack_scholar(rendered_scholar: dict, manifest_rows: list[dict], policy):
    """Pack the standalone scholar (RIDER) frames on their OWN tight trim.

    Unlike [`_pack_layers`], the rider is NOT lockstep with the giant: it packs
    its own frames directly, so each frame trims to the small scholar silhouette
    (its own atlas + `off`). Returns ``(page, rows_meta, num_pages)``."""
    from ambition_sprite2d_renderer.authoring.packer import FrameInput, pack_frames

    frames = [
        FrameInput(
            key=(r["row"], f),
            image=rendered_scholar[(r["row"], f)],
            logical_size=RIDER_FRAME,
        )
        for r in manifest_rows
        for f in range(r["frames"])
    ]
    result = pack_frames(
        frames,
        max_dim=policy.max_dim,
        page_size=policy.page_size,
        padding=1,
        trim=policy.trim,
    )
    if len(result.pages) != 1:
        raise ValueError(
            f"{RIDER_TARGET_NAME}: standalone scholar pack must fit ONE page, got "
            f"{len(result.pages)} — raise the gnu_ton page_size policy"
        )
    rows_meta = []
    for r in manifest_rows:
        rects = []
        for f in range(r["frames"]):
            pl = result.placements[(r["row"], f)]
            rect = {"x": pl.x, "y": pl.y, "w": pl.w, "h": pl.h, "fpage": pl.page}
            if pl.off_x or pl.off_y:
                rect["off"] = (pl.off_x, pl.off_y)
            rects.append(rect)
        dur = r["duration_ms"]
        rows_meta.append(
            {
                "animation": r["name"],
                "row_index": r["row"],
                "frame_count": r["frames"],
                "duration_ms": dur,
                "duration_secs": round(dur / 1000.0, 6),
                "page": result.placements[(r["row"], 0)].page if r["frames"] else 0,
                "rects": rects,
            }
        )
    return result.pages[0], rows_meta, len(result.pages)


def build_spritesheet(outdir: Path) -> List[Path]:
    """Render all animation frames and emit runtime sheets + RON metadata.

    Emits:
      - `<target>_full_spritesheet.png`   (every layer composited)
      - `<target>_body_spritesheet.png`   (everything except hands / VFX)
      - `<target>_hands_spritesheet.png`  (hands + attack VFX only)
      - `<target>_spritesheet.png`        (back-compat alias of the full sheet)
      - `<target>_spritesheet.ron`        (runtime frame + body_metrics data)
      - `<target>_actor.ron`              (actor catalog sidecar)
      - `<target>_hitboxes_debug.png`     (review-only overlay, generated only)
    """
    max_frames = max(frames for _, frames, _ in ANIMATIONS)
    rows = len(ANIMATIONS)

    # Pass 1: render every frame of every layer into memory + collect the
    # design-space anchors (gameplay hitboxes) on the full pass. We render the
    # fused layers (full/body/hands) PLUS the scholar-less `giant_body` (ADR 0020
    # MOUNT) lockstep, and the centered standalone `scholar` (RIDER) separately.
    rendered: dict = {layer: {} for layer in _LOCKSTEP_LAYERS}
    rendered_scholar: dict = {}
    manifest = {
        "target": TARGET_NAME,
        "frame_size": [FRAME_W, FRAME_H],
        "rows": [],
        "layers": list(_LAYERS),
    }
    parts: dict = {}
    for row_idx, (anim_name, frame_count, duration_ms) in enumerate(ANIMATIONS):
        for f in range(frame_count):
            for layer in _LOCKSTEP_LAYERS:
                pass_parts = parts if layer == "full" else None
                rendered[layer][(row_idx, f)] = draw_frame(
                    anim_name, f, frame_count, layer=layer, parts=pass_parts
                )
        manifest["rows"].append(
            {
                "name": anim_name,
                "row": row_idx,
                "frames": frame_count,
                "duration_ms": duration_ms,
            }
        )
        print(f"  [{row_idx + 1}/{rows}] {anim_name} ({frame_count} frames)")
    rider_rows: list[dict] = []
    for row_idx, (name, frame_count, duration_ms) in enumerate(RIDER_ROWS):
        for f in range(frame_count):
            rendered_scholar[(row_idx, f)] = _scholar.render_frame(
                Canvas, name, f, frame_count, RIDER_FRAME, RIDER_PX_PER_UNIT, SUPERSAMPLE
            )
        rider_rows.append({"name": name, "row": row_idx, "frames": frame_count, "duration_ms": duration_ms})

    # Pass 2: lockstep alpha-trim + MaxRects-pack the fused + giant_body layers
    # onto one tight page each (shared placement → the runtime addresses body +
    # hands with one flat index + trim). `policy_for` is the single data-driven
    # pack source.
    policy = policy_for(TARGET_NAME)
    layer_pages, rows_meta, num_pages = _pack_layers(
        rendered, manifest["rows"], policy, layers=_LOCKSTEP_LAYERS
    )

    outputs: List[Path] = []
    for layer in _LAYERS:
        path = outdir / f"{TARGET_NAME}_{layer}_spritesheet.png"
        layer_pages[layer][0].save(str(path), "PNG")
        outputs.append(path)

    # Back-compat alias: keep `<target>_spritesheet.png` pointing at the full
    # sheet (catalog id `gnu_ton`); it shares the body/hands packed layout so the
    # one published record drives all three textures.
    alias_path = outdir / f"{TARGET_NAME}_spritesheet.png"
    layer_pages["full"][0].save(str(alias_path), "PNG")
    outputs.append(alias_path)

    parts_doc = {
        "target": TARGET_NAME,
        "frame_size": [FRAME_W, FRAME_H],
        "design_origin": [OX, OY],
        "coordinate_space": (
            "design-space origin at frame center; y-positive = down. "
            "Runtime collision_anchor places this origin at the entity transform."
        ),
        "anchors": parts,
    }

    page_names = [f"{TARGET_NAME}_spritesheet.png"] + [
        f"{TARGET_NAME}_spritesheet.{k}.png" for k in range(1, num_pages)
    ]
    ron_path = outdir / f"{TARGET_NAME}_spritesheet.ron"
    ron_path.write_text(
        _runtime_spritesheet_ron(rows_meta, parts_doc, page_names), encoding="utf8"
    )
    outputs.append(ron_path)

    actor_path = _write_actor_contract(outdir, manifest, ron_path)
    outputs.append(actor_path)

    # ── ADR 0020 MOUNT: giant_gnu (scholar-less body + shared hands) ──────────
    # The giant_body layer lockstep-packed with the fused sheet, so it reuses
    # the SAME rows_meta (identical placement) and the same runtime body_metrics
    # (same giant). giant_gnu_body = the scholar-less body page; giant_gnu_hands
    # = the (identical) hands page; the alias composites the two (hands z-front).
    giant_body_page = layer_pages[_GIANT_BODY_LAYER][0]
    giant_hands_page = layer_pages["hands"][0]
    giant_body_path = outdir / f"{GIANT_TARGET_NAME}_body_spritesheet.png"
    giant_body_page.save(str(giant_body_path), "PNG")
    outputs.append(giant_body_path)
    giant_hands_path = outdir / f"{GIANT_TARGET_NAME}_hands_spritesheet.png"
    giant_hands_page.save(str(giant_hands_path), "PNG")
    outputs.append(giant_hands_path)
    # The giant's own sheet is its BODY: its two fists are separate bodies the
    # scholar conducts (`giant_gnu_fist`), so drawing them here as well put four
    # fists on screen, two of which never moved.
    giant_alias_path = outdir / f"{GIANT_TARGET_NAME}_spritesheet.png"
    shutil.copyfile(giant_body_path, giant_alias_path)
    outputs.append(giant_alias_path)

    giant_page_names = [f"{GIANT_TARGET_NAME}_spritesheet.png"] + [
        f"{GIANT_TARGET_NAME}_spritesheet.{k}.png" for k in range(1, num_pages)
    ]
    outputs.extend(_publish_giant_flipbook(outdir, giant_body_page))
    giant_ron_path = outdir / f"{GIANT_TARGET_NAME}_spritesheet.ron"
    # The giant's body IS its art: the authored box of the beast and its chest
    # (`giant_art.BODY_BBOX`: shoulders to hooves, not the head, the horns or
    # the tail), so the runtime sizes it from the drawing and it stands where
    # it is drawn. The fused sheet's per-row head hurtboxes are not
    # carried: the giant is the scholar's mount, not the thing you hit.
    giant_ron_path.write_text(
        _runtime_spritesheet_ron(
            _with_seam_anchors(rows_meta, _giant_seams, FRAME_SIZE, _giant_surfaces),
            parts_doc,
            giant_page_names,
            target=GIANT_TARGET_NAME,
            metrics_ron=_authored_body_metrics_ron(_giant.BODY_BBOX),
        ),
        encoding="utf8",
    )
    outputs.append(giant_ron_path)
    giant_manifest = {
        "target": GIANT_TARGET_NAME,
        "frame_size": [FRAME_W, FRAME_H],
        "rows": manifest["rows"],
        "layers": [_GIANT_BODY_LAYER, "hands"],
    }
    outputs.append(
        _write_actor_contract(
            outdir,
            giant_manifest,
            giant_ron_path,
            target=GIANT_TARGET_NAME,
            actor_metadata=GIANT_ACTOR_METADATA,
        )
    )

    # The hands page is cataloged as its own Hall character
    # (`npc_giant_gnu_hands` in character_catalog.ron), which asks for a
    # manifest of its own. It is lockstep-packed with the giant, so it carries
    # the same rows_meta — only the page it names differs.
    hands_target = f"{GIANT_TARGET_NAME}_hands"
    hands_ron_path = outdir / f"{hands_target}_spritesheet.ron"
    hands_ron_path.write_text(
        _runtime_spritesheet_ron(
            rows_meta,
            parts_doc,
            [f"{hands_target}_spritesheet.png"]
            + [f"{hands_target}_spritesheet.{k}.png" for k in range(1, num_pages)],
            target=hands_target,
        ),
        encoding="utf8",
    )
    outputs.append(hands_ron_path)

    # ── ADR 0020 RIDER: gnu_ton_rider (scholar alone, own tight-trim sheet) ───
    # Packed SEPARATELY from the giant (its own atlas/off), so it is NOT lockstep
    # and carries none of the giant's body_metrics.
    rider_page, rider_rows_meta, rider_num_pages = _pack_scholar(
        rendered_scholar, rider_rows, policy
    )
    rider_path = outdir / f"{RIDER_TARGET_NAME}_spritesheet.png"
    rider_page.save(str(rider_path), "PNG")
    outputs.append(rider_path)
    rider_page_names = [f"{RIDER_TARGET_NAME}_spritesheet.png"] + [
        f"{RIDER_TARGET_NAME}_spritesheet.{k}.png" for k in range(1, rider_num_pages)
    ]
    rider_ron_path = outdir / f"{RIDER_TARGET_NAME}_spritesheet.ron"
    rider_rest = [
        rendered_scholar[(0, f)] for f in range(RIDER_ROWS[0][1])
    ]
    rider_ron_path.write_text(
        _runtime_spritesheet_ron(
            rider_rows_meta,
            parts_doc,
            rider_page_names,
            target=RIDER_TARGET_NAME,
            frame_size=RIDER_FRAME,
            metrics_ron=_authored_body_metrics_ron(_union_bbox(rider_rest)),
        ),
        encoding="utf8",
    )
    outputs.append(rider_ron_path)
    rider_manifest = {
        "target": RIDER_TARGET_NAME,
        "frame_size": list(RIDER_FRAME),
        "rows": rider_rows,
        "layers": [_SCHOLAR_LAYER],
    }
    outputs.append(
        _write_actor_contract(
            outdir,
            rider_manifest,
            rider_ron_path,
            target=RIDER_TARGET_NAME,
            actor_metadata=RIDER_ACTOR_METADATA,
        )
    )

    outputs.extend(build_fist_sheet(outdir, policy))

    # G3 NOTE: the per-frame hand hit-geometry (`_hand_hit_frames` /
    # `gnu_hand_*` in `_gnu_ton_body_metrics`) is intentionally LEFT in place —
    # its removal is coupled to G3's StrikeRect teardown, not this split.

    # Review-only hitbox overlay: composite the full-layer frames into a plain
    # GRID (human-only, never a GPU texture) so the per-frame box coordinates
    # read against an untrimmed canvas.
    grid_full = Image.new("RGBA", (max_frames * FRAME_W, rows * FRAME_H), (0, 0, 0, 0))
    for (row_idx, f), img in rendered["full"].items():
        grid_full.paste(img, (f * FRAME_W, row_idx * FRAME_H))
    debug_path = build_hitbox_debug(outdir, grid_full, manifest, parts_doc)
    outputs.append(debug_path)

    return outputs


# ── The fist, alone ──────────────────────────────────────────────────────────
# A frame that holds one `draw_hand` with room for its impact glow below.
FIST_FRAME = _giant.FIST_FRAME
# Its rows (`giant_art.FIST_ROWS`): `rest` idles, `fall` is a fist that comes
# down, `hit` is the flinch when the player strikes it, `stuck` is a fist in
# the floor that pulls to come free. `through_*` is the far side of the punch
# of phase 1, and `none` is a fist that is not there.
FIST_ANIMATIONS: List[Tuple[str, int, int]] = list(_giant.FIST_ROWS)


def draw_fist_frame(anim: str, frame_idx: int, frame_count: int) -> Image.Image:
    """One frame of the right fist, alone (the left fist is its mirror)."""
    return _giant.render_fist(anim, frame_idx, frame_count)


def build_fist_sheet(outdir: Path, policy) -> List[Path]:
    """Render, pack and describe the lone-fist sheet (`giant_gnu_fist`)."""
    from ambition_sprite2d_renderer.authoring.packer import FrameInput, pack_frames

    rendered = {
        (row, f): draw_fist_frame(name, f, count)
        for row, (name, count, _) in enumerate(FIST_ANIMATIONS)
        for f in range(count)
    }
    result = pack_frames(
        [
            FrameInput(key=key, image=image, logical_size=FIST_FRAME)
            for key, image in rendered.items()
        ],
        max_dim=policy.max_dim,
        page_size=policy.page_size,
        padding=1,
        trim=policy.trim,
    )
    if len(result.pages) != 1:
        raise ValueError(f"{FIST_TARGET_NAME}: must pack onto ONE page")
    rows_meta = []
    for row, (name, count, dur) in enumerate(FIST_ANIMATIONS):
        rects = []
        for f in range(count):
            pl = result.placements[(row, f)]
            rect = {"x": pl.x, "y": pl.y, "w": pl.w, "h": pl.h, "fpage": pl.page}
            if pl.off_x or pl.off_y:
                rect["off"] = (pl.off_x, pl.off_y)
            rects.append(rect)
        rows_meta.append(
            {
                "animation": name,
                "row_index": row,
                "frame_count": count,
                "duration_ms": dur,
                "duration_secs": round(dur / 1000.0, 6),
                "page": 0,
                "rects": rects,
            }
        )
    page_path = outdir / f"{FIST_TARGET_NAME}_spritesheet.png"
    result.pages[0].save(str(page_path), "PNG")
    ron_path = outdir / f"{FIST_TARGET_NAME}_spritesheet.ron"
    ron_path.write_text(
        _runtime_spritesheet_ron(
            _with_seam_anchors(rows_meta, _giant.fist_seams, FIST_FRAME),
            {},
            [f"{FIST_TARGET_NAME}_spritesheet.png"],
            target=FIST_TARGET_NAME,
            frame_size=FIST_FRAME,
            # The fist's body is its mitt, not the fore arm behind it.
            metrics_ron=_authored_body_metrics_ron(_giant.FIST_BBOX),
        ),
        encoding="utf8",
    )
    manifest = {
        "target": FIST_TARGET_NAME,
        "frame_size": list(FIST_FRAME),
        "rows": [
            {"name": n, "row": i, "frames": c, "duration_ms": d}
            for i, (n, c, d) in enumerate(FIST_ANIMATIONS)
        ],
        "layers": ["fist"],
    }
    actor_path = _write_actor_contract(
        outdir,
        manifest,
        ron_path,
        target=FIST_TARGET_NAME,
        actor_metadata=FIST_ACTOR_METADATA,
    )
    return [page_path, ron_path, actor_path]


HURTBOX_OUTLINE = (0, 230, 255, 235)
HURTBOX_FILL = (0, 230, 255, 42)
HITBOX_OUTLINE = (255, 60, 60, 245)
HITBOX_FILL = (255, 60, 60, 62)
LABEL_FILL = (255, 255, 255, 230)

_ROW_METRIC_KEYS = {
    "rest": ("rest",),
    "hand_slam": ("hand_slam", "gnu_hand_slam", "gnu_shockwave"),
    "hand_sweep": ("hand_sweep", "gnu_hand_sweep"),
    "head_down": ("head_down", "gnu_head_descent"),
    "hit": ("hit",),
}


def _box_parts_for_frame(box: dict, frame_index: int) -> list[dict]:
    frames = box.get("frames")
    if frames:
        frame_box = frames[min(frame_index, len(frames) - 1)]
        return list(frame_box.get("parts", []))
    return list(box.get("parts", []))


def _draw_metric_parts(
    draw: ImageDraw.ImageDraw,
    frame_x: int,
    frame_y: int,
    parts: list[dict],
    *,
    is_hitbox: bool,
) -> None:
    outline = HITBOX_OUTLINE if is_hitbox else HURTBOX_OUTLINE
    fill = HITBOX_FILL if is_hitbox else HURTBOX_FILL
    prefix = "X" if is_hitbox else "H"
    for part in parts:
        x = int(part["x"])
        y = int(part["y"])
        w = int(part["w"])
        h = int(part["h"])
        if w <= 0 or h <= 0:
            continue
        rect = (frame_x + x, frame_y + y, frame_x + x + w - 1, frame_y + y + h - 1)
        draw.rectangle(rect, fill=fill, outline=outline, width=2)
        name = str(part.get("name", ""))
        if name:
            draw.text(
                (frame_x + x + 3, frame_y + y + 2), f"{prefix} {name}", fill=LABEL_FILL
            )


def build_hitbox_debug(
    outdir: Path, full_sheet: Image.Image, manifest: dict, parts_doc: dict
) -> Path:
    """Write a per-frame visual review of the exact RON hit/hurt boxes."""
    metrics = _gnu_ton_body_metrics(parts_doc)
    overlay = Image.new("RGBA", full_sheet.size, (0, 0, 0, 0))
    draw = blending_draw(overlay)
    for row in manifest["rows"]:
        anim = row["name"]
        row_index = int(row["row"])
        frame_count = int(row["frames"])
        metric_keys = _ROW_METRIC_KEYS.get(anim, ())
        if not metric_keys:
            continue
        for frame_index in range(frame_count):
            frame_x = frame_index * FRAME_W
            frame_y = row_index * FRAME_H
            for metric_key in metric_keys:
                metric = metrics.get(metric_key, {})
                hurtbox = metric.get("hurtbox")
                hitbox = metric.get("hitbox")
                # Draw the dangerous hitbox first, then the smaller damageable
                # hurtbox on top. This keeps the review image readable when
                # both boxes track the same moving GNU-ton head.
                if hitbox:
                    _draw_metric_parts(
                        draw,
                        frame_x,
                        frame_y,
                        _box_parts_for_frame(hitbox, frame_index),
                        is_hitbox=True,
                    )
                if hurtbox:
                    _draw_metric_parts(
                        draw,
                        frame_x,
                        frame_y,
                        _box_parts_for_frame(hurtbox, frame_index),
                        is_hitbox=False,
                    )
            draw.text(
                (frame_x + 6, frame_y + 6), f"{anim} #{frame_index}", fill=LABEL_FILL
            )
    debug = Image.alpha_composite(full_sheet.convert("RGBA"), overlay)
    path = outdir / HITBOX_DEBUG_FILE
    debug.save(path, "PNG")
    return path


def _write_actor_contract(
    outdir: Path,
    manifest: dict,
    ron_path: Path,
    *,
    target: str = TARGET_NAME,
    actor_metadata: dict = ACTOR_METADATA,
) -> Path:
    from ambition_sprite2d_renderer.authoring.actor_contract import (
        write_actor_contract_for_tackon,
    )

    return write_actor_contract_for_tackon(
        target=target,
        image_out=outdir / f"{target}_spritesheet.png",
        sheet_ron_out=ron_path,
        manifest=manifest,
        actor_metadata=actor_metadata,
    )


def build_canonical(outdir: Path) -> Path:
    """Render a single canonical reference pose (full layer)."""
    img = draw_frame("rest", 0, ANIMATIONS[0][1], layer="full")
    path = outdir / f"{TARGET_NAME}_canonical.png"
    big = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    big.save(str(path), "PNG")
    return path


def build_preview_labeled(outdir: Path) -> Path:
    """Render a labeled preview strip showing all animations (full layer)."""
    frames_per_row = [frame_count for _, frame_count, _ in ANIMATIONS]
    preview_h = len(ANIMATIONS) * (FRAME_H // 2 + 18)
    preview_w = max(frames_per_row) * (FRAME_W // 2)
    preview = Image.new("RGBA", (preview_w, preview_h), (30, 22, 15, 255))

    for row_idx, (anim_name, frame_count, _) in enumerate(ANIMATIONS):
        y_base = row_idx * (FRAME_H // 2 + 18)
        for f in range(frame_count):
            img = draw_frame(anim_name, f, frame_count, layer="full")
            thumb = img.resize((FRAME_W // 2, FRAME_H // 2), Image.LANCZOS)
            x = f * (FRAME_W // 2)
            preview.paste(thumb, (x, y_base), thumb)

    path = outdir / f"{TARGET_NAME}_preview_labeled.png"
    preview.save(str(path), "PNG")
    return path


def render_outputs(outdir: Path, quick: bool = False) -> List[Path]:
    """Render all outputs into outdir. Returns list of generated paths."""
    outdir.mkdir(parents=True, exist_ok=True)
    print(f"[{TARGET_NAME}] rendering to {outdir}/")

    paths = []
    print("  spritesheets (full / body / hands)...")
    paths.extend(build_spritesheet(outdir))

    review_dir = outdir / "review"
    review_dir.mkdir(exist_ok=True)
    print("  canonical...")
    paths.append(build_canonical(review_dir))

    if not quick:
        print("  preview...")
        paths.append(build_preview_labeled(review_dir))

    print(f"  done. {len(paths)} files.")
    return paths


def install_outputs(render_dir: Path, install_dir: Path) -> List[Path]:
    """Copy generated PNG + manifest into the sandbox assets tree."""
    install_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    pages = sorted(p.name for p in render_dir.glob(f"{GIANT_TARGET_NAME}_parts_*.png"))
    for fname in list(OUTPUT_FILES) + pages:
        src = render_dir / fname
        if not src.exists():
            print(f"  [WARN] missing: {src.name}")
            continue
        dst = install_dir / fname
        shutil.copy2(src, dst)
        copied.append(dst)
        try:
            display = dst.relative_to(TOOL_ROOT)
        except ValueError:
            display = dst
        print(f"  installed: {display}")
    return copied


if __name__ == "__main__":
    import argparse, sys

    p = argparse.ArgumentParser()
    p.add_argument("outdir", nargs="?", default="generated/gnu_ton_boss")
    p.add_argument("--quick", action="store_true")
    args = p.parse_args()
    paths = render_outputs(Path(args.outdir), quick=args.quick)
    for path in paths:
        print(path)
