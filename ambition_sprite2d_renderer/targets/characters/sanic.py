"""Procedural "Sanic" sprite sheets — the crudely-drawn Sonic meme, authored as
a full dual-purpose fighter/platformer body, plus its **Super Sanic**
transformation.

The whole joke is that Sanic is Sonic drawn *badly* in a paint program: a
small lumpy blue head on a neck over a big round body, two mismatched beady
eyes with a fat black nose wedged between them, thick ugly head spikes, ONE
huge weird spike off the middle of the back, stick arms, long awful legs, and
oversized red shoes. Every silhouette is a hand-jittered polygon (`_blob` /
`_wobble`) so the outline visibly wobbles; the jitter is deterministic
(seeded off vertex index) so the sheet is reproducible across regen runs.

The sheet is deliberately over-authored so the Ambition engine can express
*two* classic games from one body's data:

  * a Sonic-style platformer — run / spin-dash / rolling ball / ledge grab
    / wall cling, with the jump and every curled pose in BALL form; and
  * a Smash-style fighter — jab/punch, side/up/down tilts, the five aerials
    (nair/fair/bair/uair/dair), a spin special, shield, dodge-roll, and the
    ledge/getup-attack options.

Two render paths compose everything:

  * `_render_humanoid` — the posed body. Each animation hands it concrete limb
    targets (front/back hand + ankle, offsets from the hips), a lean/crouch, a
    face, and an optional effect (swoosh / shield / stars / dust).
  * `_ball_frame` / `_draw_spin_ball` — the curled ball. Per Jon: the jump and
    every curled pose are the ball, and the ball SPINS COMPLETELY AROUND — the
    spin angle sweeps a whole number of full turns across the row so it loops
    seamlessly, and an asymmetric highlight quill + red streak make the full
    rotation actually read.

Super Sanic is the same body, same moveset, same geometry — re-skinned. All
drawing is parameterized by a `Skin` (palette + `spikes_up` + `aura`), so the
transformation is literally a different skin: gold palette, spikes standing UP,
red eyes, and a golden aura. Both forms register as targets from this one module
(`TARGETS`), sharing every pose and every hurt/hitbox.

Per-pose hurtboxes and per-attack hitboxes are authored into each sheet RON via
`animation_key_map` + `attack_hitboxes`, so the body is usable as a real
fighter, not just an animated picture.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from PIL import Image, ImageColor, ImageDraw, ImageFilter

from ...authoring import rigdoc, shape_rig
from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

FRAME_SIZE = (128, 128)
SUPER = 4
W, H = FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER
BASE_X = 60.0
GROUND_Y = 112.0

INK = "#0b0b0b"     # heavy wobbly outline — shared by both forms

#: How much of the raised spikes' authored reach actually fits the frame.
#:
#: The drawing canvas is the logical frame, so raised spikes drawn past `y = 0`
#: are clipped. This factor was selected with `clipped_frame_edges`:
#:
#:     x1.00   61 of 181 frames cut        x0.80    2 cut
#:     x0.85    4 of 181 cut               x0.76    0 cut
#:
#:  base Sanic is the control and is clean at 0 of 181 — same body, same
#: canvas, spikes swept BACK instead of up. So this is the raised fan's reach and
#: nothing else, which is why one factor on one branch is the whole fix.
#:
#:  not a round number and not a taste call: 0.76 is the largest value
#: measured that leaves every frame whole, and anything above it cuts something.
#:
#:  and it is NOT fixable by moving the body down or growing the frame.
#: `auto_crop` is off for this sheet precisely so `ATTACK_HITBOXES` coordinates
#: match draw space, so shifting the art or resizing the frame silently moves
#: every authored hitbox with respect to the drawing. The spikes are the only
#: thing here that can give.
SUPER_SPIKE_FIT = 0.76


# --- Skins --------------------------------------------------------------------


@dataclass(frozen=True)
class Skin:
    """A palette + a couple of transformation flags. Everything the drawing
    reads about colour/silhouette comes from here, so a new form is just a new
    Skin (no drawing code changes)."""

    body: str          # main blue/gold
    body_dk: str       # spikes + lower body
    muzzle: str        # muzzle + arms + belly
    muzzle_dk: str
    eye: str           # eye white / gloves
    pupil: str         # pupil colour (black normally, red for super)
    shoe: str
    shoe_dk: str
    buckle: str
    accent: str        # impact stars / sparkles
    shield: str = "#7fd8ff"
    nose: str = "#141414"
    spikes_up: bool = False       # raise the head + back spikes (super)
    aura: Optional[str] = None    # golden glow behind the body (super)


NORMAL = Skin(
    body="#2f6fd0", body_dk="#245aad",
    muzzle="#f0c08a", muzzle_dk="#d99f63",
    eye="#fbfbfb", pupil=INK,
    shoe="#d5342c", shoe_dk="#a5211c", buckle="#f2f2f2",
    accent="#e7c53a",
)

SUPER_SKIN = Skin(
    body="#ffe24a", body_dk="#eeb70e",
    muzzle="#ffeec2", muzzle_dk="#e6c877",
    eye="#fbfbfb", pupil="#d81f1f",       # red eyes
    shoe="#d5342c", shoe_dk="#a5211c", buckle="#f2f2f2",   # red shoes stay
    accent="#fff6b0",
    spikes_up=True,
    aura="#ffe36b",
)


# --- Curled poses (rendered as the spinning ball) -----------------------------
BALL_ANIMS: Dict[str, float] = {
    # anim -> number of FULL turns across the row (integer => seamless loop).
    "jump": 1.0,
    "dash": 2.0,
    "dash_startup": 1.0,
    "ball": 2.0,
    "air_neutral": 1.0,
    "air_down": 2.0,
    "special": 2.0,
}


# --- Primitives ---------------------------------------------------------------


def _rgba(color: str, alpha: int = 255) -> RGBA:
    r, g, b = ImageColor.getrgb(color)
    return (r, g, b, alpha)


def _s(v: float) -> int:
    return int(round(v * SUPER))


def _pt(x: float, y: float) -> Tuple[int, int]:
    return (_s(x), _s(y))


def _box(x1: float, y1: float, x2: float, y2: float) -> Tuple[int, int, int, int]:
    return (_s(x1), _s(y1), _s(x2), _s(y2))


def _downsample(img: Image.Image) -> Image.Image:
    return rigdoc.downsampled_canvas(img, FRAME_SIZE, Image.Resampling.LANCZOS)


def _jitter(i: int, salt: float) -> Tuple[float, float]:
    """Deterministic per-vertex offset in [-1, 1]^2 — a cheap hash of the vertex
    index so the hand-drawn wobble is stable across regen runs (no RNG)."""
    a = math.sin(i * 12.9898 + salt * 3.17) * 43758.5453
    b = math.sin(i * 78.2330 + salt * 1.71) * 12543.1234
    return ((a - math.floor(a)) * 2.0 - 1.0, (b - math.floor(b)) * 2.0 - 1.0)


def _wobble(pts: Sequence[Point], amp: float, salt: float) -> List[Point]:
    out: List[Point] = []
    for i, (x, y) in enumerate(pts):
        jx, jy = _jitter(i, salt)
        out.append((x + jx * amp, y + jy * amp))
    return out


def _blob(cx: float, cy: float, rx: float, ry: float, salt: float, amp: float = 1.6, n: int = 22) -> List[Point]:
    """A wobbly closed ellipse-ish polygon — a mouse-drawn circle."""
    pts: List[Point] = []
    for i in range(n):
        ang = math.tau * i / n
        jx, jy = _jitter(i, salt)
        pts.append((cx + math.cos(ang) * (rx + jx * amp), cy + math.sin(ang) * (ry + jy * amp)))
    return pts


def _poly(draw: ImageDraw.ImageDraw, pts: Sequence[Point], fill: RGBA, outline: Optional[RGBA] = None, width: float = 2.0) -> None:
    scaled = [_pt(x, y) for x, y in pts]
    draw.polygon(scaled, fill=fill, outline=outline, width=_s(width) if outline else 0)


def _spike(cx: float, cy: float, dx: float, dy: float, length: float, width: float, salt: float, wob: float = 2.6) -> List[Point]:
    """A fat, tapering, wobbly quill from `(cx, cy)` along direction `(dx, dy)`:
    a wide wobbly base bulging at ~45% then tapering to the tip. Direction-based
    so a form can aim its spikes anywhere (back for Sanic, up for Super Sanic)."""
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    px, py = -uy, ux

    def along(t: float, w: float) -> Point:
        return (cx + ux * length * t + px * w, cy + uy * length * t + py * w)

    pts = [
        (cx + px * width, cy + py * width),
        along(0.45, width * 0.85),
        (cx + ux * length, cy + uy * length),
        along(0.45, -width * 0.85),
        (cx - px * width, cy - py * width),
    ]
    return _wobble(pts, wob, salt)


# --- Effects (translucent overlays, each one piece) ---------------------------


def _draw_speed_lines(img: Image.Image, skin: Skin, cx: float, cy: float, phase: float, intensity: float, direction: Point = (-1.0, 0.0), name: str = "speed_lines") -> None:
    """Six speed lines trailing along ``direction``: painted along +x and
    turned to it."""
    pattern = int(phase * 3) % 12
    hx, hy = HOME

    def paint(canvas, d) -> None:
        for i in range(6):
            off = (i - 2.5) * 10.0
            length = 26.0 + 18.0 * intensity + ((i * 7 + pattern) % 12)
            x0, y0 = hx + 18.0, hy + off
            col = _rgba(skin.eye if i % 2 == 0 else skin.body, int(150 * intensity))
            d.line(_box(x0, y0, x0 + length, y0), fill=col, width=_s(2.2))

    degrees = math.degrees(math.atan2(direction[1], direction[0]))
    _put(img, ("speed_lines", skin, intensity, pattern), paint, (cx, cy), name, degrees)


def _swoosh(img: Image.Image, skin: Skin, cx: float, cy: float, r: float, a0: float, a1: float) -> None:
    hx, hy = HOME

    def paint(canvas, d) -> None:
        d.arc(_box(hx - r, hy - r, hx + r, hy + r), a0, a1, fill=_rgba(skin.eye, 225), width=_s(3.2))
        d.arc(_box(hx - r + 2.2, hy - r + 2.2, hx + r - 2.2, hy + r - 2.2), a0 + 8, a1 - 8, fill=_rgba(skin.body, 180), width=_s(1.6))

    _put(img, ("swoosh", skin, r, a0, a1), paint, (cx, cy), "swoosh")


def _stars(img: Image.Image, skin: Skin, cx: float, cy: float, salt: float, n: int = 4) -> None:
    hx, hy = HOME

    def paint(canvas, d) -> None:
        for i in range(n):
            jx, jy = _jitter(i, salt)
            sx, sy = hx + jx * 7.0, hy + jy * 7.0
            r = 2.4 + (i % 2) * 1.2
            d.line(_box(sx - r, sy, sx + r, sy), fill=_rgba(skin.accent, 235), width=_s(1.4))
            d.line(_box(sx, sy - r, sx, sy + r), fill=_rgba(skin.accent, 235), width=_s(1.4))

    _put(img, ("stars", skin, salt, n), paint, (cx, cy), "stars")


def _shield_bubble(img: Image.Image, skin: Skin, cx: float, cy: float, r: float) -> None:
    hx, hy = HOME

    def paint(canvas, d) -> None:
        d.ellipse(_box(hx - r, hy - r, hx + r, hy + r), fill=_rgba(skin.shield, 70), outline=_rgba("#c8f2ff", 170), width=_s(1.6))

    _put(img, ("shield", skin, r), paint, (cx, cy), "shield")


def _dust(img: Image.Image, cx: float, cy: float, salt: float) -> None:
    hx, hy = HOME

    def paint(canvas, d) -> None:
        for i in range(4):
            jx, _ = _jitter(i, salt)
            px = hx + (i - 1.5) * 8.0 + jx * 2.0
            r = 3.0 + (i % 2) * 1.5
            d.ellipse(_box(px - r, hy - r * 0.6, px + r, hy + r * 0.6), fill=_rgba("#d8d8d8", 150))

    _put(img, ("dust", salt), paint, (cx, cy), "dust")


def _aura(img: Image.Image, skin: Skin, cx: float, cy: float, r: float, salt: float) -> None:
    """Super Sanic's golden glow + drifting sparkles, drawn behind the body.
    A no-op for skins without an aura. The glow is one piece; each sparkle is
    one piece, moved each frame (seeded by ``salt``)."""
    if not skin.aura:
        return
    hx, hy = HOME

    def glow(canvas, d) -> None:
        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        gd = blending_draw(layer)
        gd.ellipse(_box(hx - r, hy - r * 1.15, hx + r, hy + r * 1.15), fill=_rgba(skin.aura, 95))
        canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(radius=SUPER * 3.2)))

    _put(img, ("aura", skin.aura, r), glow, (cx, cy), "aura")
    for i in range(7):
        jx, jy = _jitter(i, salt + 3)
        rr = 1.6 + (i % 2) * 1.3

        def sparkle(canvas, d, rr=rr) -> None:
            d.line(_box(hx - rr, hy, hx + rr, hy), fill=_rgba("#fffbe0", 235), width=_s(1.2))
            d.line(_box(hx, hy - rr, hx, hy + rr), fill=_rgba("#fffbe0", 235), width=_s(1.2))

        _put(img, ("sparkle", rr), sparkle, (cx + jx * (r * 0.95), cy + jy * (r * 1.05)), f"sparkle_{i}")


# --- Body parts ---------------------------------------------------------------


def _draw_shoe(draw: ImageDraw.ImageDraw, skin: Skin, cx: float, cy: float, salt: float, tilt: float = 0.0) -> None:
    """One oversized red shoe pointing right, with the white sock stripe."""
    toe, heel, sole = cx + 12.0, cx - 9.0, cy + 6.0
    pts = [
        (heel, cy - 4.0), (cx - 2.0, cy - 6.0 + tilt), (cx + 6.0, cy - 5.0 + tilt),
        (toe, cy - 1.0 + tilt), (toe + 1.5, cy + 2.5 + tilt), (toe - 3.0, sole),
        (heel + 1.0, sole), (heel - 1.5, cy + 1.0),
    ]
    _poly(draw, _wobble(pts, 1.2, salt), _rgba(skin.shoe), _rgba(INK), 2.0)
    draw.line(_box(heel + 3.0, cy + 1.0, toe - 3.0, cy + 1.5 + tilt), fill=_rgba(skin.buckle), width=_s(2.2))
    draw.line(_box(heel + 1.0, sole - 0.5, toe - 3.0, sole - 0.5), fill=_rgba(skin.shoe_dk), width=_s(1.4))


def _draw_leg(draw: ImageDraw.ImageDraw, hip: Point, ankle: Point, shade: str, salt: float, bend: float = 0.0) -> None:
    """One long, awful, spindly leg: a thin wobbly two-segment line with a
    knobbly kicked-out knee."""
    hpx, hpy = hip
    apx, apy = ankle
    kx, ky = (hpx + apx) / 2.0 + bend, (hpy + apy) / 2.0 + 1.0
    pts = _wobble([hip, (kx, ky), ankle], 1.6, salt)
    scaled = [_pt(x, y) for x, y in pts]
    draw.line(scaled, fill=_rgba(shade), width=_s(2.6), joint="curve")
    draw.line(scaled, fill=_rgba(INK), width=_s(0.8), joint="curve")
    _poly(draw, _blob(kx, ky, 2.2, 2.2, salt + 1, amp=0.6, n=8), _rgba(shade), _rgba(INK), 1.0)


def _arm_to(draw: ImageDraw.ImageDraw, skin: Skin, shoulder: Point, hand: Point, salt: float, bend: float = 3.0) -> None:
    """A thin tan arm from `shoulder` to `hand` with an auto-computed elbow (a
    perpendicular kick of `bend`), capped by a crude white glove blob."""
    sx, sy = shoulder
    hx, hy = hand
    mx, my = (sx + hx) / 2.0, (sy + hy) / 2.0
    dx, dy = hx - sx, hy - sy
    length = math.hypot(dx, dy) or 1.0
    px, py = -dy / length, dx / length
    ex, ey = mx + px * bend, my + py * bend
    draw.line([_pt(sx, sy), _pt(ex, ey), _pt(hx, hy)], fill=_rgba(skin.muzzle), width=_s(3.2), joint="curve")
    draw.line([_pt(sx, sy), _pt(ex, ey), _pt(hx, hy)], fill=_rgba(INK), width=_s(0.9), joint="curve")
    _poly(draw, _blob(hx, hy, 3.2, 2.9, salt, amp=0.7, n=10), _rgba(skin.eye), _rgba(INK), 1.3)


def _put_shoe(img: Image.Image, skin: Skin, at: Point, salt: float, tilt: float, name: str) -> None:
    """One shoe as a piece, one per (whole-pixel) toe tilt."""
    tilt = float(round(tilt))
    hx, hy = HOME
    _put(img, ("shoe", skin, salt, tilt), lambda canvas, d: _draw_shoe(d, skin, hx, hy, salt, tilt=tilt), at, name)


def _put_leg(img: Image.Image, hip: Point, ankle: Point, shade: str, salt: float, bend: float, name: str) -> None:
    """One spindly leg: two strokes and the knobbly knee piece."""
    kx, ky = (hip[0] + ankle[0]) / 2.0 + bend, (hip[1] + ankle[1]) / 2.0 + 1.0
    a, k, b = _wobble([hip, (kx, ky), ankle], 1.6, salt)
    _limb(img, a, k, b, shade, 2.6, 0.8, name)
    hx, hy = HOME
    _put(img, ("knee", shade, salt), lambda canvas, d: _poly(d, _blob(hx, hy, 2.2, 2.2, salt + 1, amp=0.6, n=8), _rgba(shade), _rgba(INK), 1.0), (kx, ky), f"{name}_knee")


def _put_arm(img: Image.Image, skin: Skin, shoulder: Point, hand: Point, salt: float, bend: float, name: str) -> None:
    """One stick arm (``_arm_to``): two strokes to an elbow kicked out by
    ``bend``, and the glove piece."""
    sx, sy = shoulder
    hx, hy = hand
    dx, dy = hx - sx, hy - sy
    length = math.hypot(dx, dy) or 1.0
    px, py = -dy / length, dx / length
    elbow = ((sx + hx) / 2.0 + px * bend, (sy + hy) / 2.0 + py * bend)
    _limb(img, shoulder, elbow, hand, skin.muzzle, 3.2, 0.9, name)
    ox, oy = HOME
    _put(img, ("glove", skin, salt), lambda canvas, d: _poly(d, _blob(ox, oy, 3.2, 2.9, salt, amp=0.7, n=10), _rgba(skin.eye), _rgba(INK), 1.3), hand, f"{name}_glove")


def _draw_head_spikes(draw: ImageDraw.ImageDraw, skin: Skin, hx: float, hy: float, tr: float, salt: float) -> None:
    """Three thick head spikes. Sanic sweeps them back; Super Sanic raises them
    UP (the transformation's signature).

    ⚠ the raised fan is scaled by [`SUPER_SPIKE_FIT`]; read it before retuning
    these lengths, because the authored numbers do not fit the frame.
    """
    if skin.spikes_up:
        # rooted on top of the head, standing up (fanned).
        specs = [((hx - 6, hy - 8), (-0.5, -1.0), 24.0, 5.0),
                 ((hx - 1, hy - 11), (0.0, -1.1), 28.0, 5.4),
                 ((hx + 4, hy - 9), (0.5, -1.0), 24.0, 5.0)]
        ext = tr * 0.4
        fit = SUPER_SPIKE_FIT
    else:
        # rooted on the back of the head, swept back-left.
        specs = [((hx - 4, hy - 8), (-0.92, -0.45), 24.0, 5.0),
                 ((hx - 6, hy - 1), (-1.0, 0.05), 26.0, 5.4),
                 ((hx - 4, hy + 7), (-0.75, 0.5), 22.0, 5.0)]
        ext = tr
        fit = 1.0
    for i, ((rx, ry), (dx, dy), length, wdt) in enumerate(specs):
        _poly(draw, _spike(rx, ry, dx, dy, (length + ext) * fit, wdt, salt + i * 3), _rgba(skin.body_dk), _rgba(INK), 2.6)


def _draw_back_spike(draw: ImageDraw.ImageDraw, skin: Skin, torso_cx: float, torso_cy: float, tr: float, salt: float) -> None:
    """The one big weird spike off the MIDDLE OF THE BACK. Sanic sweeps it
    back-and-up; Super Sanic stands it straight UP off the upper back."""
    if skin.spikes_up:
        reach = (48.0 + tr * 0.5) * SUPER_SPIKE_FIT
        _poly(draw, _spike(torso_cx - 4.0, torso_cy - 14.0, 0.05, -1.0, reach, 10.0, salt, wob=3.0), _rgba(skin.body_dk), _rgba(INK), 2.8)
    else:
        _poly(draw, _spike(torso_cx - 8.0, torso_cy - 4.0, -0.95, -0.28, 44.0 + tr, 9.5, salt, wob=3.0), _rgba(skin.body_dk), _rgba(INK), 2.8)


def _draw_face(draw: ImageDraw.ImageDraw, skin: Skin, hx: float, hy: float, salt: float, look: float, mouth: str) -> None:
    """Beady, close-set, mostly-pupil eyes with the fat nose wedged *between*
    them. `look` shifts the pupils (-1 back .. +1 forward)."""
    _poly(draw, _blob(hx + 7.0, hy + 6.0, 9.0, 8.0, salt + 5, amp=1.4, n=18), _rgba(skin.muzzle), _rgba(INK), 2.0)

    lx, ly, lr = hx + 2.5, hy - 3.0, 3.8
    rx, ry, rr = hx + 8.5, hy - 4.0, 3.3
    _poly(draw, _blob(lx, ly, lr, lr, salt + 1, amp=0.6, n=12), _rgba(skin.eye), _rgba(INK), 1.6)
    _poly(draw, _blob(rx, ry, rr, rr, salt + 2, amp=0.6, n=12), _rgba(skin.eye), _rgba(INK), 1.6)
    _poly(draw, _blob(hx + 5.2, hy - 1.0, 3.0, 2.8, salt + 9, amp=0.7, n=12), _rgba(skin.nose), None)

    if mouth == "dead":
        for (ex, ey, er) in ((lx, ly, lr), (rx, ry, rr)):
            draw.line(_box(ex - er, ey - er, ex + er, ey + er), fill=_rgba(INK), width=_s(1.4))
            draw.line(_box(ex - er, ey + er, ex + er, ey - er), fill=_rgba(INK), width=_s(1.4))
    else:
        pdx = look * 1.2
        draw.ellipse(_box(lx - 2.0 + pdx, ly - 2.0, lx + 2.0 + pdx, ly + 2.0), fill=_rgba(skin.pupil))
        draw.ellipse(_box(rx - 1.8 + pdx, ry - 1.8, rx + 1.8 + pdx, ry + 1.8), fill=_rgba(skin.pupil))
        draw.ellipse(_box(lx - 1.2 + pdx, ly - 1.2, lx - 0.2 + pdx, ly - 0.2), fill=_rgba(skin.eye))

    if mouth == "grin":
        draw.arc(_box(hx + 1.0, hy + 4.0, hx + 14.0, hy + 13.0), 10, 150, fill=_rgba(INK), width=_s(1.6))
    elif mouth == "open":
        _poly(draw, _wobble([(hx + 3.0, hy + 7.0), (hx + 12.0, hy + 6.0), (hx + 11.0, hy + 12.0), (hx + 4.0, hy + 12.0)], 0.8, salt), _rgba("#7a2b2b"), _rgba(INK), 1.2)
    elif mouth == "hurt":
        draw.arc(_box(hx + 2.0, hy + 8.0, hx + 13.0, hy + 15.0), 190, 350, fill=_rgba(INK), width=_s(1.6))
    else:  # flat little smirk
        draw.line(_box(hx + 2.5, hy + 9.0, hx + 11.0, hy + 8.0), fill=_rgba(INK), width=_s(1.4))


# --- Pieces -------------------------------------------------------------------
#
# Sanic is drawn as a rig: each rigid thing (the head with its face and
# spikes, the torso, the back spike, a shoe, a glove, a knee, a quill, an
# effect) is painted ONCE by its old painter on a scratch canvas with its
# anchor at ``HOME``, cut to what it covers, and placed (and turned) through
# ``shape_rig``. Arms and legs are strokes: one piece per (quarter-pixel)
# length, turned to the bone. A part flipbook stores each once. Things rigid
# to each other (the six quills, the two shoe smudges) are ONE piece.
#
# The old sheet boiled: every polygon's wobble was seeded by the frame index,
# so every frame was a new picture. A piece's wobble is seeded by ``SALT``
# instead (the hand-drawn wobble stays, the boil goes). Super Sanic's
# sparkles still drift: each sparkle is one piece moved per frame.

SALT = 1.0
#: Where a piece's anchor is painted on the scratch canvas (frame pixels).
HOME = (float(FRAME_SIZE[0]), float(FRAME_SIZE[1]))
_PIECES: Dict[tuple, Optional[Tuple[Image.Image, Point]]] = {}


def _piece(key: tuple, paint) -> Optional[Tuple[Image.Image, Point]]:
    """The raster ``paint(canvas, draw)`` paints with its anchor at ``HOME``,
    cut to its box, and the anchor in it (super pixels); ``None`` when it
    paints nothing. ``key`` must name everything ``paint`` reads."""
    if key not in _PIECES:
        canvas = Image.new("RGBA", (2 * W, 2 * H), (0, 0, 0, 0))
        paint(canvas, blending_draw(canvas))
        box = canvas.getchannel("A").getbbox()
        _PIECES[key] = None if box is None else (canvas.crop(box), (HOME[0] * SUPER - box[0], HOME[1] * SUPER - box[1]))
    return _PIECES[key]


def _put(img: Image.Image, key: tuple, paint, at: Point, name: str, degrees: float = 0.0) -> None:
    """Place the piece ``key`` with its anchor at ``at`` (frame pixels)."""
    part = _piece(key, paint)
    if part is not None:
        shape_rig.place(img, part, (at[0] * SUPER, at[1] * SUPER), degrees, name)


def _stroke(img: Image.Image, a: Point, b: Point, color: str, width: float, ink_width: float, name: str, start_cap: bool = True) -> None:
    """A limb segment from ``a`` to ``b``: a ``color`` stroke with an ink line
    down its middle, as one piece turned to the segment. Without
    ``start_cap`` it starts square, so it does not cover the ink of the
    segment before it at the joint."""
    length = round(math.hypot(b[0] - a[0], b[1] - a[1]) * 4) / 4
    hx, hy = HOME

    def paint(canvas, draw) -> None:
        r = width / 2
        draw.line([_pt(hx, hy), _pt(hx + length, hy)], fill=_rgba(color), width=_s(width))
        if start_cap:
            draw.ellipse(_box(hx - r, hy - r, hx + r, hy + r), fill=_rgba(color))
        draw.ellipse(_box(hx + length - r, hy - r, hx + length + r, hy + r), fill=_rgba(color))
        draw.line([_pt(hx, hy), _pt(hx + length, hy)], fill=_rgba(INK), width=_s(ink_width))

    degrees = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
    _put(img, ("stroke", length, color, width, ink_width, start_cap), paint, a, name, degrees)


def _limb(img: Image.Image, root: Point, joint: Point, end: Point, color: str, width: float, ink_width: float, name: str) -> None:
    _stroke(img, root, joint, color, width, ink_width, f"{name}_upper")
    _stroke(img, joint, end, color, width, ink_width, f"{name}_lower", start_cap=False)


# --- The spinning ball (jump + every curled pose) -----------------------------


def _draw_spin_ball(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    skin: Skin,
    cx: float,
    cy: float,
    spin: float,
    salt: float,
    lines: Optional[str] = None,
    dust: bool = False,
    emphasize: bool = False,
    r: float = 16.0,
) -> None:
    """Sanic curled into a spinning ball. `spin` is the absolute rotation angle;
    an asymmetric highlight quill + the red streak both ride it, so a full turn
    actually reads as a full turn (not a symmetric blur). `lines` picks the
    motion context: trail / radial / down / up. Each quill, the streak, the
    shoe smudges, the face smear and the halo are painted at angle 0 and
    turned by the spin."""
    del draw
    hx, hy = HOME
    _aura(img, skin, cx, cy, r + 8.0, salt)

    if lines == "trail":
        _draw_speed_lines(img, skin, cx, cy, spin, 1.0, direction=(-1.0, -0.12))
    elif lines == "radial":
        # Six turned copies of one set (a fan painted as one piece holds
        # 20 times the texels).
        for k in range(6):
            a = k * math.tau / 6.0
            _draw_speed_lines(img, skin, cx + math.cos(a) * 2, cy + math.sin(a) * 2, spin, 0.5, direction=(math.cos(a), math.sin(a)), name=f"speed_lines_{k}")
    elif lines == "down":
        _draw_speed_lines(img, skin, cx, cy + r, spin, 1.0, direction=(0.0, 1.0))
    elif lines == "up":
        _draw_speed_lines(img, skin, cx, cy - r, spin, 0.9, direction=(0.0, -1.0))

    if dust:
        _dust(img, cx, cy + r + 2.0, SALT)

    # Radiating quill blur (6-fold, symmetric — the motion smear) and ONE
    # dominant highlight quill (asymmetric — marks the rotation): one piece,
    # painted at spin 0 and turned by the spin.
    def quills(canvas, d) -> None:
        for k in range(6):
            ang = k * math.tau / 6.0
            tip = (hx + math.cos(ang) * (r + 8.0), hy + math.sin(ang) * (r + 8.0))
            b1 = (hx + math.cos(ang - 0.30) * r, hy + math.sin(ang - 0.30) * r)
            b2 = (hx + math.cos(ang + 0.30) * r, hy + math.sin(ang + 0.30) * r)
            _poly(d, _wobble([b1, tip, b2], 1.0, SALT + k), _rgba(skin.body_dk), _rgba(INK), 1.4)
        tip = (hx + (r + 12.0), hy)
        b1 = (hx + math.cos(-0.42) * r, hy + math.sin(-0.42) * r)
        b2 = (hx + math.cos(0.42) * r, hy + math.sin(0.42) * r)
        _poly(d, _wobble([b1, tip, b2], 1.2, SALT + 20), _rgba(skin.body), _rgba(INK), 1.8)

    _put(img, ("ball_quills", skin, r), quills, (cx, cy), "quills", math.degrees(spin))

    # Ball body.
    _put(img, ("ball_body", skin, r), lambda canvas, d: _poly(d, _blob(hx, hy, r, r, SALT, amp=2.2, n=20), _rgba(skin.body), _rgba(INK), 2.4), (cx, cy), "ball")

    # Red streak wrapping the ball, starting at `spin` (rotates with the spin).
    def streak(canvas, d) -> None:
        d.arc(_box(hx - r + 1, hy - r + 1, hx + r - 1, hy + r - 1), 0, 250 if emphasize else 200, fill=_rgba(skin.shoe, 215), width=_s(3.2))

    _put(img, ("ball_streak", skin, r, emphasize), streak, (cx, cy), "streak", int(math.degrees(spin)) % 360)

    # Two shoe smudges caught mid-spin (one piece, turned by the spin) + a
    # pale face smear so the whirl reads.
    def smudges(canvas, d) -> None:
        for k in range(2):
            a = k * math.pi
            _poly(d, _blob(hx + math.cos(a) * r * 0.55, hy + math.sin(a) * r * 0.55, 4.5, 3.0, SALT + k, amp=0.8, n=10), _rgba(skin.shoe), _rgba(INK), 1.2)

    _put(img, ("ball_smudges", skin, r), smudges, (cx, cy), "smudges", math.degrees(spin))

    def smear(canvas, d) -> None:
        d.arc(_box(hx - r * 0.7, hy - r * 0.7, hx + r * 0.7, hy + r * 0.7), 0, 70, fill=_rgba(skin.muzzle, 150), width=_s(1.6))

    _put(img, ("ball_smear", skin, r), smear, (cx, cy), "smear", int(math.degrees(spin + 0.6)) % 360)

    if emphasize:
        def halo(canvas, d) -> None:
            for k in range(8):
                a = k * math.tau / 8.0
                x0, y0 = hx + math.cos(a) * (r + 6), hy + math.sin(a) * (r + 6)
                x1, y1 = hx + math.cos(a) * (r + 16), hy + math.sin(a) * (r + 16)
                d.line(_box(x0, y0, x1, y1), fill=_rgba(skin.shoe, 150), width=_s(1.6))

        _put(img, ("ball_halo", skin, r), halo, (cx, cy), "halo", math.degrees(spin * 1.5))


def _ball_frame(skin: Skin, anim: str, frame_idx: int, nframes: int) -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = blending_draw(img)
    t = frame_idx / max(1, nframes)
    salt = float(frame_idx + 1)
    turns = BALL_ANIMS[anim]
    spin = math.tau * t * turns  # completes `turns` FULL rotations across the row

    if anim == "jump":
        cx, cy = BASE_X + 2.0, GROUND_Y - 46.0
        _draw_spin_ball(img, draw, skin, cx, cy, spin, salt, lines="up", r=15.0)
    elif anim == "dash":
        cx, cy = BASE_X + 4.0, GROUND_Y - 14.0
        _draw_spin_ball(img, draw, skin, cx, cy, spin, salt, lines="trail", dust=True, r=16.0)
    elif anim == "dash_startup":
        cx, cy = BASE_X, GROUND_Y - 14.0
        _draw_spin_ball(img, draw, skin, cx, cy, spin, salt, lines="trail", dust=True, r=15.0)
    elif anim == "ball":
        cx, cy = BASE_X + 2.0, GROUND_Y - 13.0
        _draw_spin_ball(img, draw, skin, cx, cy, spin, salt, lines="trail", dust=True, r=15.0)
    elif anim == "air_neutral":
        cx, cy = BASE_X + 2.0, GROUND_Y - 42.0
        _draw_spin_ball(img, draw, skin, cx, cy, spin, salt, lines="radial", r=15.0)
    elif anim == "air_down":
        cx, cy = BASE_X + 2.0, GROUND_Y - 34.0
        _draw_spin_ball(img, draw, skin, cx, cy, spin, salt, lines="down", r=15.0)
    else:  # special — the spin attack
        cx, cy = BASE_X + 2.0, GROUND_Y - 30.0
        _draw_spin_ball(img, draw, skin, cx, cy, spin, salt, lines="radial", emphasize=True, r=17.0)

    return _downsample(img)


# --- The posed humanoid body --------------------------------------------------


def _render_humanoid(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    skin: Skin,
    salt: float,
    *,
    bob: float = 0.0,
    hips_dx: float = 0.0,
    lean: float = 0.0,
    crouch: float = 0.0,
    look: float = 0.4,
    mouth: str = "smirk",
    fh: Optional[Point] = None,   # front-hand offset (dx, dy) from hips
    bh: Optional[Point] = None,   # back-hand offset
    fa: Optional[Point] = None,   # front-ankle offset
    ba: Optional[Point] = None,   # back-ankle offset
    airborne: bool = False,
    fell: bool = False,
    leg_blur: bool = False,
    fx: Optional[str] = None,
    fx_t: float = 0.0,
) -> None:
    del draw
    hx0, hy0 = HOME
    hips_x = BASE_X + hips_dx
    hips_y = GROUND_Y - 42.0 + bob
    head_cx = hips_x + 4.0 + lean
    head_cy = hips_y - 44.0 + crouch * 16.0 + bob * 0.4
    torso_cx = hips_x + 1.0 + lean * 0.3
    torso_cy = hips_y - 6.0 + crouch * 5.0
    tr = round(lean * 0.5, 2)

    if fell:
        head_cx = hips_x - 16.0
        head_cy = hips_y + 6.0

    # Golden aura behind the whole body (super only).
    _aura(img, skin, (head_cx + torso_cx) / 2.0, (head_cy + torso_cy) / 2.0 + 4.0, 30.0, salt)

    # Default limb targets (offsets from the hips). ground contact ≈ hips_y+38.
    gy = GROUND_Y - 4.0 - hips_y
    if fh is None:
        fh = (18.0, 2.0)
    if bh is None:
        bh = (-12.0, 2.0)
    if fa is None:
        fa = (7.0, gy) if not airborne else (9.0, 30.0)
    if ba is None:
        ba = (-3.0, gy) if not airborne else (-2.0, 32.0)

    if fx == "speed":
        _draw_speed_lines(img, skin, head_cx, head_cy + 6.0, fx_t, 1.0)

    # ---- Legs + shoes ----
    if leg_blur:
        bcx, bcy = hips_x + 2.0, GROUND_Y - 8.0

        def blur(canvas, d) -> None:
            d.ellipse(_box(hx0 - 15, hy0 - 14, hx0 + 15, hy0 + 12), fill=_rgba(skin.shoe, 150))
            d.ellipse(_box(hx0 - 11, hy0 - 18, hx0 + 11, hy0 + 16), fill=_rgba(skin.shoe, 110))

        _put(img, ("leg_blur", skin), blur, (bcx, bcy), "leg_blur")
        for k in range(3):
            ang = fx_t * 3.0 + k * math.tau / 3.0
            _put_shoe(img, skin, (bcx + math.cos(ang) * 12.0, bcy + math.sin(ang) * 11.0), SALT + k, math.sin(ang) * 2.0, f"shoe_{k}")
    elif fell:
        for i, (dx, dy) in enumerate(((14.0, -4.0), (20.0, -12.0))):
            ankle = (hips_x + dx, hips_y + dy)
            _put_leg(img, (hips_x + 2.0, hips_y + 2.0), ankle, skin.muzzle if i else skin.muzzle_dk, SALT + i, 6.0, f"leg_{i}")
            _put_shoe(img, skin, (ankle[0] + 3.0, ankle[1]), SALT + i, 6.0, f"shoe_{i}")
    else:
        back_ankle = (hips_x + ba[0], hips_y + ba[1])
        front_ankle = (hips_x + fa[0], hips_y + fa[1])
        _put_leg(img, (hips_x - 1.0, hips_y + 5.0), back_ankle, skin.muzzle_dk, SALT, -3.0 + ba[0] * 0.2, "leg_0")
        _put_leg(img, (hips_x + 3.0, hips_y + 5.0), front_ankle, skin.muzzle, SALT + 3, 2.0 + fa[0] * 0.2, "leg_1")
        _put_shoe(img, skin, (back_ankle[0] + 2.0, back_ankle[1]), SALT, 0.0, "shoe_0")
        _put_shoe(img, skin, (front_ankle[0] + 2.0, front_ankle[1]), SALT + 3, 0.0, "shoe_1")

    # ---- Back arm (behind body) ----
    _put_arm(img, skin, (hips_x + 2.0, hips_y - 6.0), (hips_x + bh[0], hips_y + bh[1]), SALT + 7, -3.0, "back_arm")

    # ---- Big back spike (off the mid-back, behind torso) ----
    _put(img, ("back_spike", skin, tr), lambda canvas, d: _draw_back_spike(d, skin, hx0, hy0, tr, SALT + 4), (torso_cx, torso_cy), "back_spike")

    # ---- Neck (connects the separated head to the body): one piece per
    # (whole-pixel) length, turned from the head to the torso ----
    if not fell:
        nt = (head_cx - 1.0, head_cy + 9.0)
        nb = (torso_cx + 1.0, torso_cy - 14.0)
        length = round(math.hypot(nb[0] - nt[0], nb[1] - nt[1]))

        def neck(canvas, d) -> None:
            pts = [(hx0 - 6.0, hy0), (hx0 + 6.0, hy0), (hx0 + 9.0, hy0 + length), (hx0 - 9.0, hy0 + length)]
            _poly(d, _wobble(pts, 1.0, SALT + 12), _rgba(skin.body), _rgba(INK), 2.0)

        degrees = math.degrees(math.atan2(nb[1] - nt[1], nb[0] - nt[0])) - 90.0
        _put(img, ("neck", skin, length), neck, nt, "neck", degrees)

    # ---- Torso + belly circle ----
    def torso(canvas, d) -> None:
        _poly(d, _blob(hx0, hy0, 17.0, 18.0, SALT + 6, amp=2.0, n=20), _rgba(skin.body), _rgba(INK), 2.4)
        _poly(d, _blob(hx0 + 4.0, hy0 + 4.0, 6.0, 6.5, SALT + 11, amp=1.0, n=14), _rgba(skin.muzzle), _rgba(INK), 1.4)

    _put(img, ("torso", skin), torso, (torso_cx, torso_cy), "torso")

    # ---- Head spikes + small head + face: one piece per look ----
    look = round(look, 1)

    def head(canvas, d) -> None:
        _draw_head_spikes(d, skin, hx0, hy0, tr, SALT + 4)
        _poly(d, _blob(hx0, hy0, 14.0, 13.0, SALT, amp=1.8, n=20), _rgba(skin.body), _rgba(INK), 2.4)
        _draw_face(d, skin, hx0, hy0, SALT, look, mouth)

    _put(img, ("head", skin, tr, look, mouth), head, (head_cx, head_cy), "head")

    # ---- Front arm (over body) ----
    _put_arm(img, skin, (hips_x + 6.0, hips_y - 6.0), (hips_x + fh[0], hips_y + fh[1]), SALT + 8, 3.0, "front_arm")

    # ---- Attack / state effects rendered over the body ----
    if fx == "arc_fwd":
        _swoosh(img, skin, hips_x + 22.0, hips_y - 2.0, 16.0, -70, 70)
    elif fx == "arc_up":
        _swoosh(img, skin, hips_x + 8.0, head_cy - 6.0, 15.0, 200, 340)
    elif fx == "arc_down":
        _swoosh(img, skin, hips_x + 16.0, hips_y + 26.0, 15.0, 20, 160)
    elif fx == "kick_fwd":
        _swoosh(img, skin, hips_x + 24.0, hips_y + 10.0, 14.0, -50, 90)
    elif fx == "kick_back":
        _swoosh(img, skin, hips_x - 22.0, hips_y + 8.0, 14.0, 90, 230)
    elif fx == "stars":
        _stars(img, skin, hips_x + fh[0] + 2.0, hips_y + fh[1], SALT + 30)
    elif fx == "shield":
        _shield_bubble(img, skin, torso_cx + 1.0, torso_cy - 2.0, 26.0)
    elif fx == "dust":
        _dust(img, hips_x, GROUND_Y - 4.0, SALT + 40)


# --- Per-animation pose dispatch ----------------------------------------------


def _draw_sanic(skin: Skin, anim: str, frame_idx: int, nframes: int) -> Image.Image:
    if anim in BALL_ANIMS:
        return _ball_frame(skin, anim, frame_idx, nframes)

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = blending_draw(img)
    t = frame_idx / max(1, nframes)
    cyc = math.tau * t
    salt = float(frame_idx + 1)
    p: dict = {}

    if anim == "idle":
        sw = math.sin(cyc) * 2.0
        p = dict(bob=math.sin(cyc) * 1.6, look=0.2 + math.sin(cyc * 0.5) * 0.3,
                 fh=(18.0, 2.0 + sw), bh=(-12.0, 2.0 - sw))
    elif anim == "walk":
        step = math.sin(cyc)
        p = dict(bob=abs(math.sin(cyc)) * 2.2, look=0.5,
                 fh=(18.0, 2.0 + step * 4.0), bh=(-12.0, 2.0 - step * 4.0),
                 fa=(7.0 + step * 8.0, GROUND_Y - 4.0 - (GROUND_Y - 42.0)),
                 ba=(-3.0 - step * 7.0, GROUND_Y - 4.0 - (GROUND_Y - 42.0)))
    elif anim == "run":
        p = dict(bob=abs(math.sin(cyc * 2)) * 1.6, lean=9.0, look=0.9, mouth="grin",
                 leg_blur=True, fx="speed", fx_t=cyc,
                 fh=(20.0, -2.0 + math.sin(cyc * 2) * 6.0), bh=(-14.0, -1.0 - math.sin(cyc * 2) * 6.0))
    elif anim == "crouch":
        p = dict(crouch=1.0, look=0.3, fh=(11.0, 8.0), bh=(-8.0, 8.0),
                 fa=(11.0, GROUND_Y - 4.0 - (GROUND_Y - 42.0)), ba=(-9.0, GROUND_Y - 4.0 - (GROUND_Y - 42.0)))
    elif anim == "fall":
        p = dict(bob=2.0 + math.sin(cyc) * 1.0, lean=-3.0, airborne=True, look=-0.2, mouth="hurt",
                 fh=(16.0, -6.0), bh=(-14.0, -6.0), fa=(9.0, 30.0), ba=(-2.0, 32.0))
    elif anim == "land_hard":
        p = dict(crouch=0.9, look=0.3, mouth="open", fx="dust",
                 fh=(16.0, 7.0), bh=(-14.0, 7.0))
    elif anim == "land_recovery":
        rise = 1.0 - t
        p = dict(crouch=0.5 * rise, look=0.4, fh=(16.0, 4.0 * rise + 2.0), bh=(-13.0, 4.0 * rise + 2.0))
    elif anim == "skid":  # braking against travel — lean back hard, dig the heels in
        j = math.sin(cyc * 2) * 1.5
        p = dict(crouch=0.3, lean=-14.0, look=0.6, mouth="open", fx="dust",
                 fh=(18.0, -8.0 + j), bh=(-16.0, 4.0 - j),
                 fa=(16.0, GROUND_Y - 4.0 - (GROUND_Y - 42.0)), ba=(-10.0, GROUND_Y - 4.0 - (GROUND_Y - 42.0)))
    elif anim == "slash":  # jab
        ext = math.sin(min(1.0, t * 1.6) * math.pi)
        p = dict(look=0.7, mouth="grin", fx="arc_fwd" if ext > 0.4 else None,
                 fh=(16.0 + ext * 10.0, -2.0), bh=(-12.0, 2.0))
    elif anim == "punch":
        ext = math.sin(min(1.0, t * 1.8) * math.pi)
        p = dict(look=0.8, mouth="open", fx="stars" if ext > 0.6 else None,
                 fh=(16.0 + ext * 14.0, 0.0), bh=(-12.0, 3.0))
    elif anim == "attack_side":  # forward tilt — big swipe
        ext = math.sin(min(1.0, t * 1.5) * math.pi)
        p = dict(lean=3.0, look=0.8, mouth="grin", fx="arc_fwd" if ext > 0.35 else None,
                 fh=(18.0 + ext * 12.0, -4.0 + ext * 2.0), bh=(-12.0, 3.0))
    elif anim == "attack_up":
        ext = math.sin(min(1.0, t * 1.5) * math.pi)
        p = dict(look=0.4, mouth="grin", fx="arc_up" if ext > 0.35 else None,
                 fh=(8.0, -22.0 - ext * 8.0), bh=(-11.0, 2.0))
    elif anim == "attack_down":  # low sweeping kick
        ext = math.sin(min(1.0, t * 1.5) * math.pi)
        p = dict(crouch=0.5, look=0.6, mouth="grin", fx="arc_down" if ext > 0.35 else None,
                 fh=(10.0, 8.0), bh=(-8.0, 8.0),
                 fa=(14.0 + ext * 12.0, 36.0), ba=(-8.0, 38.0))
    elif anim == "air_forward":
        ext = math.sin(min(1.0, t * 1.5) * math.pi)
        p = dict(airborne=True, lean=4.0, look=0.8, mouth="grin", fx="kick_fwd" if ext > 0.35 else None,
                 fh=(14.0, -4.0), bh=(-12.0, -4.0), fa=(16.0 + ext * 12.0, 8.0), ba=(-4.0, 26.0))
    elif anim == "air_back":
        ext = math.sin(min(1.0, t * 1.5) * math.pi)
        p = dict(airborne=True, lean=-4.0, look=-0.4, mouth="grin", fx="kick_back" if ext > 0.35 else None,
                 fh=(12.0, -4.0), bh=(-14.0, -4.0), fa=(6.0, 24.0), ba=(-14.0 - ext * 10.0, 6.0))
    elif anim == "air_up":
        ext = math.sin(min(1.0, t * 1.5) * math.pi)
        p = dict(airborne=True, look=0.3, mouth="grin", fx="arc_up" if ext > 0.35 else None,
                 fh=(10.0, -18.0), bh=(-10.0, -14.0), fa=(6.0, -18.0 - ext * 8.0), ba=(-3.0, 26.0))
    elif anim == "block":  # shield
        p = dict(crouch=0.25, look=0.2, mouth="smirk", fx="shield",
                 fh=(10.0, 6.0), bh=(-8.0, 6.0))
    elif anim == "wall_grab":  # cling to a wall on the right
        p = dict(lean=6.0, look=0.6, mouth="smirk", airborne=True,
                 fh=(20.0, -8.0), bh=(16.0, 2.0), fa=(18.0, 20.0), ba=(14.0, 32.0))
    elif anim == "wall_jump":  # push off the wall, launch away
        p = dict(lean=-6.0, look=-0.3, mouth="open", airborne=True, fx="dust",
                 fh=(-16.0, -6.0), bh=(-18.0, 2.0), fa=(-10.0, 24.0), ba=(4.0, 28.0))
    elif anim == "ledge_grab":  # hanging from a ledge above
        p = dict(bob=10.0, airborne=True, look=0.2, mouth="smirk",
                 fh=(14.0, -14.0), bh=(6.0, -14.0), fa=(6.0, 34.0), ba=(-2.0, 36.0))
    elif anim == "ledge_climb":
        pull = t
        p = dict(bob=10.0 - pull * 10.0, airborne=True, look=0.4, mouth="grin",
                 fh=(12.0, -12.0 + pull * 8.0), bh=(4.0, -12.0 + pull * 8.0),
                 fa=(8.0, 30.0 - pull * 6.0), ba=(-2.0, 34.0 - pull * 6.0))
    elif anim == "ledge_getup":
        rise = t
        p = dict(crouch=0.8 * (1.0 - rise), look=0.4, mouth="smirk",
                 fh=(14.0, 4.0), bh=(-10.0, 4.0))
    elif anim == "ledge_getup_attack":
        ext = math.sin(min(1.0, t * 1.6) * math.pi)
        p = dict(crouch=0.3, lean=3.0, look=0.8, mouth="grin",
                 fx="arc_fwd" if ext > 0.4 else ("stars" if ext > 0.2 else None),
                 fh=(18.0 + ext * 12.0, -2.0), bh=(-10.0, 4.0))
    elif anim == "ledge_roll":
        p = dict(crouch=0.6, lean=6.0, look=0.4, mouth="open",
                 fh=(12.0, 8.0), bh=(-6.0, 8.0),
                 fa=(12.0, 34.0), ba=(-6.0, 36.0))
    elif anim == "hit":
        j = math.sin(cyc * 3) * 2.0
        p = dict(bob=j, lean=-6.0, look=-0.6, mouth="hurt",
                 fh=(14.0, -6.0 + j), bh=(-16.0, -4.0 - j))
    elif anim == "death":
        prog = min(1.0, t * 1.4)
        p = dict(bob=prog * 6.0, lean=-14.0 * prog, look=0.0, mouth="dead",
                 fell=prog > 0.55, fh=(14.0, -6.0), bh=(-16.0, -4.0))
    elif anim == "taunt":  # smug victory
        p = dict(bob=math.sin(cyc * 2) * 2.6, look=0.8, mouth="grin",
                 fh=(20.0, -24.0), bh=(-12.0, 2.0))
    elif anim == "interact":
        reach = math.sin(min(1.0, t * 1.4) * math.pi)
        p = dict(look=0.5, mouth="smirk", fh=(16.0 + reach * 8.0, 4.0), bh=(-11.0, 3.0))
    else:  # safety fallback
        p = dict()

    _render_humanoid(img, draw, skin, salt, **p)
    return _downsample(img)


# ---- Rows ---------------------------------------------------------------------
# (name, frame_count, frame_duration_ms). Names are the canonical CharacterAnim
# aliases (crates/.../character_sprites/anim/mod.rs::from_name) so the runtime
# resolves each pose; unlisted poses fall back through `base_pose`.
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 140),
    ("walk", 8, 90),
    ("run", 8, 70),
    ("crouch", 2, 160),
    ("dash_startup", 6, 70),
    ("dash", 6, 60),
    ("ball", 6, 60),
    ("jump", 6, 80),
    ("fall", 4, 90),
    ("land_hard", 3, 70),
    ("land_recovery", 4, 90),
    ("skid", 3, 80),
    ("slash", 5, 60),
    ("punch", 4, 55),
    ("attack_side", 6, 70),
    ("attack_up", 6, 70),
    ("attack_down", 6, 70),
    ("air_neutral", 6, 70),
    ("air_forward", 5, 70),
    ("air_back", 5, 70),
    ("air_up", 5, 70),
    ("air_down", 6, 70),
    ("special", 8, 70),
    ("block", 3, 120),
    ("wall_grab", 3, 140),
    ("wall_jump", 4, 80),
    ("ledge_grab", 3, 150),
    ("ledge_climb", 5, 90),
    ("ledge_getup", 5, 90),
    ("ledge_getup_attack", 6, 70),
    ("ledge_roll", 5, 80),
    ("hit", 4, 100),
    ("death", 8, 110),
    ("taunt", 6, 120),
    ("interact", 5, 110),
]

# Generic gameplay keys for per-pose combat metadata (hurtboxes auto-derived per
# key; hitboxes authored below). Keyed row -> generic key (== row name).
ANIMATION_KEY_MAP: Dict[str, str] = {
    name: name
    for name, _n, _ms in ROWS
    if name in {
        "idle", "walk", "run", "crouch", "jump", "fall", "dash", "ball", "skid",
        "slash", "punch", "attack_side", "attack_up", "attack_down",
        "air_neutral", "air_forward", "air_back", "air_up", "air_down",
        "special", "block", "wall_grab", "ledge_grab", "ledge_getup_attack",
        "hit",
    }
}

# Authored strike volumes, in frame pixel coords (auto_crop=False keeps these in
# the same space we draw in). Approximate first-pass geometry — tune later.
ATTACK_HITBOXES: Dict[str, dict] = {
    "slash": {"bbox": {"x": 78, "y": 56, "w": 30, "h": 26}},
    "punch": {"bbox": {"x": 80, "y": 58, "w": 30, "h": 24}},
    "attack_side": {"bbox": {"x": 80, "y": 54, "w": 34, "h": 28}},
    "attack_up": {"bbox": {"x": 54, "y": 8, "w": 30, "h": 36}},
    "attack_down": {"bbox": {"x": 66, "y": 92, "w": 36, "h": 20}},
    "air_neutral": {"bbox": {"x": 44, "y": 52, "w": 40, "h": 40}},
    "air_forward": {"bbox": {"x": 78, "y": 64, "w": 32, "h": 26}},
    "air_back": {"bbox": {"x": 22, "y": 60, "w": 32, "h": 26}},
    "air_up": {"bbox": {"x": 52, "y": 14, "w": 30, "h": 32}},
    "air_down": {"bbox": {"x": 44, "y": 70, "w": 38, "h": 44}},
    "special": {"bbox": {"x": 38, "y": 58, "w": 46, "h": 46}},
    "ledge_getup_attack": {"bbox": {"x": 74, "y": 56, "w": 34, "h": 28}},
}


def _melee_events(active_from: float, active_to: float, source: str) -> List[dict]:
    return [
        {"t": max(0.0, active_from - 0.12), "event": "telegraph_peak", "source": source},
        {"t": active_from, "event": "hitbox_active_start", "source": source},
        {"t": active_to, "event": "hitbox_active_end", "source": source},
    ]


def _animation_bindings(source: str) -> dict:
    """Bindings for BOTH game styles: platformer locomotion + a full Smash-style
    melee/aerial/special/ledge kit, with active-frame windows on each strike."""
    return {
        "default": {"animation": "idle", "events": []},
        # platformer locomotion
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "locomotion.crouch": {"animation": "crouch", "events": []},
        "locomotion.jump": {"animation": "jump", "events": []},
        "locomotion.fall": {"animation": "fall", "events": []},
        "locomotion.land": {"animation": "land_hard", "events": [{"t": 0.0, "event": "land_impact", "source": source}]},
        "locomotion.land_recover": {"animation": "land_recovery", "events": []},
        "locomotion.wall_slide": {"animation": "wall_grab", "events": []},
        "locomotion.wall_cling": {"animation": "wall_grab", "events": []},
        "locomotion.wall_jump": {"animation": "wall_jump", "events": [{"t": 0.1, "event": "wall_launch", "source": source}]},
        "locomotion.ledge_grab": {"animation": "ledge_grab", "events": []},
        "locomotion.ledge_climb": {"animation": "ledge_climb", "events": []},
        # ground melee
        "action.melee.primary": {"animation": "slash", "events": _melee_events(0.34, 0.62, source)},
        "action.melee.punch": {"animation": "punch", "events": _melee_events(0.40, 0.60, source)},
        "action.melee.side": {"animation": "attack_side", "events": _melee_events(0.30, 0.60, source)},
        "action.melee.up": {"animation": "attack_up", "events": _melee_events(0.32, 0.58, source)},
        "action.melee.down": {"animation": "attack_down", "events": _melee_events(0.34, 0.60, source)},
        # aerials
        "action.air.neutral": {"animation": "air_neutral", "events": _melee_events(0.15, 0.85, source)},
        "action.air.forward": {"animation": "air_forward", "events": _melee_events(0.30, 0.58, source)},
        "action.air.back": {"animation": "air_back", "events": _melee_events(0.30, 0.58, source)},
        "action.air.up": {"animation": "air_up", "events": _melee_events(0.32, 0.58, source)},
        "action.air.down": {"animation": "air_down", "events": _melee_events(0.20, 0.80, source)},
        # specials (the spin)
        "action.special.spin": {"animation": "special", "events": _melee_events(0.10, 0.92, source)},
        "action.special.dash": {"animation": "dash", "events": [{"t": 0.30, "event": "dash_commit", "source": source}]},
        "action.special.dash_charge": {"animation": "dash_startup", "events": []},
        # defense / ledge options
        "action.defense.block": {"animation": "block", "events": []},
        "action.defense.roll": {"animation": "ball", "events": [{"t": 0.15, "event": "iframes_start", "source": source}, {"t": 0.75, "event": "iframes_end", "source": source}]},
        "action.ledge.getup": {"animation": "ledge_getup", "events": []},
        "action.ledge.getup_attack": {"animation": "ledge_getup_attack", "events": _melee_events(0.36, 0.64, source)},
        "action.ledge.roll": {"animation": "ledge_roll", "events": []},
        # reactions / emotes
        "reaction.hit": {"animation": "hit", "events": []},
        "reaction.death": {"animation": "death", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
    }


ACTOR_METADATA_SANIC = {
    "actor": {"character_id": "npc_sanic", "display_name": "Sanic"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "locomotion_hint": "Run",
        "traits": ["npc", "meme", "fast", "runner", "fighter", "beast"],
    },
    "capabilities": {
        "traversal": {"walk": True, "jump": True, "climb": True, "fly": False, "swim": None, "use_lifts": None, "door_access": []},
        "interactions": {"talk": True, "trade": None, "carry": None, "open_doors": []},
    },
    "brain": {"default_preset": "wanderer_puppy_slug"},
    "actions": {"default_preset": "peaceful_float"},
    "animation_bindings": _animation_bindings("sanic"),
    "tags": ["meme", "fast", "runner", "fighter", "platformer"],
}
ACTOR_METADATA_SANIC.update(
    {
        "authoring_description": (
            "Sanic is the deliberately crude internet-meme mutation of Sonic the "
            "Hedgehog: frantic, badly proportioned, overconfident, and defined by the "
            "demand to go fast rather than by polished mascot heroism."
        ),
        "gameplay_description": (
            "Use as an absurdly fast runner, rival, playable fighter, or unstable speed "
            "tutorial. Movement should outrun composure, with skids, wall actions, spin "
            "attacks, and dialogue that treats standing still as abuse."
        ),
        "dialogue_hints": {
            "barks": [
                "The pedestal asked me to idle. I have reported it for abuse.",
                "I can stop whenever I want. I do not want.",
                "Fast enough to outrun the answer.",
            ]
        },
    }
)

# Super Sanic — the transformation. Same body/moveset/geometry; the golden,
# spikes-up, invincible power form. It flies and hits harder; the sprite is the
# same body re-skinned so a runtime transformation just swaps the sheet.
ACTOR_METADATA_SUPER = {
    "actor": {"character_id": "npc_super_sanic", "display_name": "Super Sanic"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "locomotion_hint": "Fly",
        "traits": ["npc", "meme", "fast", "runner", "fighter", "beast", "super", "transformation", "invincible", "flight"],
    },
    "capabilities": {
        "traversal": {"walk": True, "jump": True, "climb": True, "fly": True, "swim": None, "use_lifts": None, "door_access": []},
        "interactions": {"talk": True, "trade": None, "carry": None, "open_doors": []},
    },
    "brain": {"default_preset": "wanderer_puppy_slug"},
    "actions": {"default_preset": "peaceful_float"},
    "animation_bindings": _animation_bindings("super_sanic"),
    "tags": ["meme", "fast", "runner", "fighter", "platformer", "super", "transformation"],
}
ACTOR_METADATA_SUPER.update(
    {
        "authoring_description": (
            "Super Sanic is the golden, airborne transformation of the Sanic meme, "
            "combining the crude Sonic parody with the invincible super-form spectacle "
            "of collected power and impossible speed."
        ),
        "gameplay_description": (
            "Use as a temporary transformation, boss phase, or overpowered unlock. He "
            "should fly, ignore ordinary hazards, and behave as though reality itself is "
            "too slow to enforce its rules."
        ),
        "dialogue_hints": {
            "barks": [
                "I am not glowing. The air is falling behind.",
                "Immortality is a budget with excellent music.",
                "The universe may submit a written request.",
            ]
        },
    }
)


def _render_form(target_name: str, skin: Skin, actor_metadata: dict, out_dir: str | Path) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
        return _draw_sanic(skin, animation, frame_idx, nframes)

    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=target_name,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        label_width=118,
        # Keep frames uncropped so authored hitbox coords match our draw space.
        auto_crop=False,
        actor_metadata=actor_metadata,
        animation_key_map=ANIMATION_KEY_MAP,
        attack_hitboxes=ATTACK_HITBOXES,
    )
    parts = publish_rig_flipbook(target_name, ROWS, render_frame, outputs, frame_transform, out_dir)
    return [outputs[k] for k in ("canonical", "canonical_transparent", "spritesheet", "yaml", "ron", "actor", "preview")] + list(
        parts.values()
    )


def render_sanic(out_dir: str | Path, **opts) -> List[Path]:
    return _render_form("sanic", NORMAL, ACTOR_METADATA_SANIC, out_dir)


def render_super_sanic(out_dir: str | Path, **opts) -> List[Path]:
    return _render_form("super_sanic", SUPER_SKIN, ACTOR_METADATA_SUPER, out_dir)


# Both forms register as targets from this one module (same drawing + moveset,
# different Skin). `super_sanic` is Sanic's transformation, shipped as its own
# swappable sheet.
TARGETS = {
    "sanic": {"render": render_sanic, "actor_metadata": ACTOR_METADATA_SANIC},
    "super_sanic": {"render": render_super_sanic, "actor_metadata": ACTOR_METADATA_SUPER},
}


# Backwards-compatible module-level entry (some callers import `render_frame`).
def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    return _draw_sanic(NORMAL, animation, frame_idx, nframes)
