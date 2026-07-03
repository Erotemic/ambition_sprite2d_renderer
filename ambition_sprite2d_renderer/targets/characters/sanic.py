"""Procedural "Sanic" sprite sheet — the crudely-drawn Sonic meme.

The whole joke is that Sanic is Sonic drawn *badly* in a paint program: a
lumpy blue blob head, two wonky quills, a bulbous peach muzzle with a fat
black nose, two mismatched googly eyes that don't line up, stick arms, and
oversized red shoes. So this target deliberately fights the renderer's
instinct toward clean geometry:

  * Every silhouette is a hand-jittered polygon (`_blob` / `_wobble`) rather
    than a crisp ellipse — the outline visibly wobbles like a mouse-drawn
    curve. The jitter is deterministic (seeded off vertex index + a per-frame
    salt) so the sheet is reproducible across regen runs.
  * Fills are flat MS-Paint colors with a thick, slightly-too-heavy black
    outline. No gradients, no glow.
  * The two eyes are different sizes and sit at different heights — the
    signature "derp".

Recognizability still matters: blue body, peach muzzle + fat nose, big white
eyes, red shoes, and the "GOTTA GO FAST" run where the legs dissolve into a
red figure-of-eight blur with speed lines. Signature move is the spin-ball
(`dash` / `slash`).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageColor, ImageDraw

from ...authoring.sheet_build import build_sheet

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "sanic"
SHEET_FILES = [
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
]

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_sanic",
        "display_name": "Sanic",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "locomotion_hint": "Run",
        "traits": ["npc", "meme", "fast", "runner", "beast"],
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": True,
            "climb": None,
            "fly": False,
            "swim": None,
            "use_lifts": None,
            "door_access": [],
        },
        "interactions": {
            "talk": True,
            "trade": None,
            "carry": None,
            "open_doors": [],
        },
    },
    "brain": {"default_preset": "wanderer_puppy_slug"},
    "actions": {"default_preset": "peaceful_float"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "locomotion.jump": {"animation": "jump", "events": []},
        "locomotion.fall": {"animation": "fall", "events": []},
        "action.special.dash": {
            "animation": "dash",
            "events": [
                {"t": 0.30, "event": "dash_commit", "source": "sanic"},
            ],
        },
        "action.melee.primary": {
            "animation": "slash",
            "events": [
                {"t": 0.20, "event": "telegraph_peak", "source": "sanic"},
                {"t": 0.36, "event": "hitbox_active_start", "source": "sanic"},
                {"t": 0.66, "event": "hitbox_active_end", "source": "sanic"},
            ],
        },
    },
    "tags": ["meme", "fast", "runner"],
}

# (name, frame_count, frame_duration_ms)
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 140),
    ("walk", 8, 90),
    ("run", 8, 70),
    ("dash", 6, 70),
    ("jump", 4, 90),
    ("fall", 4, 90),
    ("slash", 6, 80),
    ("hit", 4, 100),
    ("death", 8, 110),
    ("celebrate", 6, 120),
]

FRAME_SIZE = (128, 128)
SUPER = 4
W, H = FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER

# --- Sanic palette (flat, MS-Paint-crude) -------------------------------------
BLUE = "#2f6fd0"        # body
BLUE_DK = "#245aad"     # lower-body / shadow-ish fill (still flat)
INK = "#0b0b0b"         # heavy wobbly outline
SKIN = "#f0c08a"        # muzzle + arms (Sonic tan)
SKIN_DK = "#d99f63"
NOSE = "#141414"
EYE = "#fbfbfb"
SHOE = "#d5342c"        # red shoes
SHOE_DK = "#a5211c"
BUCKLE = "#f2f2f2"      # shoe stripe / sock
GOLD = "#e7c53a"


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
    return img.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


def _jitter(i: int, salt: float) -> Tuple[float, float]:
    """Deterministic per-vertex offset in [-1, 1]^2 — a cheap hash of the
    vertex index so the "hand-drawn" wobble is stable across regen runs
    (no RNG, no `random` seeding to thread through)."""
    a = math.sin(i * 12.9898 + salt * 3.17) * 43758.5453
    b = math.sin(i * 78.2330 + salt * 1.71) * 12543.1234
    return ((a - math.floor(a)) * 2.0 - 1.0, (b - math.floor(b)) * 2.0 - 1.0)


def _wobble(pts: Sequence[Point], amp: float, salt: float) -> List[Point]:
    out: List[Point] = []
    for i, (x, y) in enumerate(pts):
        jx, jy = _jitter(i, salt)
        out.append((x + jx * amp, y + jy * amp))
    return out


def _blob(
    cx: float, cy: float, rx: float, ry: float, salt: float, amp: float = 1.6, n: int = 22
) -> List[Point]:
    """A wobbly closed ellipse-ish polygon — a mouse-drawn circle."""
    pts: List[Point] = []
    for i in range(n):
        ang = math.tau * i / n
        jx, jy = _jitter(i, salt)
        pts.append(
            (cx + math.cos(ang) * (rx + jx * amp), cy + math.sin(ang) * (ry + jy * amp))
        )
    return pts


def _poly(
    draw: ImageDraw.ImageDraw,
    pts: Sequence[Point],
    fill: RGBA,
    outline: RGBA = None,
    width: float = 2.0,
) -> None:
    scaled = [_pt(x, y) for x, y in pts]
    draw.polygon(scaled, fill=fill, outline=outline, width=_s(width) if outline else 0)


def _draw_speed_lines(
    img: Image.Image, cx: float, cy: float, phase: float, intensity: float
) -> None:
    """Horizontal MS-Paint dashes trailing behind, drawn onto a translucent
    layer (alpha-composited so the dashes don't clobber the body alpha)."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    for i in range(6):
        yy = cy - 26.0 + i * 10.0 + math.sin(phase + i) * 1.5
        x_end = cx - 18.0 - (i % 3) * 6.0
        x_start = x_end - (26.0 + 18.0 * intensity) - ((i * 7 + int(phase * 3)) % 12)
        col = _rgba(EYE if i % 2 == 0 else BLUE, int(150 * intensity))
        d.line(_box(x_start, yy, x_end, yy), fill=col, width=_s(2.2))
    img.alpha_composite(layer)


def _draw_shoe(
    draw: ImageDraw.ImageDraw, cx: float, cy: float, salt: float, tilt: float = 0.0
) -> None:
    """One oversized red shoe pointing right, with the white sock/stripe."""
    toe = cx + 12.0
    heel = cx - 9.0
    sole = cy + 6.0
    pts = [
        (heel, cy - 4.0),
        (cx - 2.0, cy - 6.0 + tilt),
        (cx + 6.0, cy - 5.0 + tilt),
        (toe, cy - 1.0 + tilt),
        (toe + 1.5, cy + 2.5 + tilt),
        (toe - 3.0, sole),
        (heel + 1.0, sole),
        (heel - 1.5, cy + 1.0),
    ]
    _poly(draw, _wobble(pts, 1.2, salt), _rgba(SHOE), _rgba(INK), 2.0)
    # White stripe/buckle across the shoe.
    draw.line(_box(heel + 3.0, cy + 1.0, toe - 3.0, cy + 1.5 + tilt), fill=_rgba(BUCKLE), width=_s(2.2))
    # Sole shadow.
    draw.line(_box(heel + 1.0, sole - 0.5, toe - 3.0, sole - 0.5), fill=_rgba(SHOE_DK), width=_s(1.4))


def _draw_arm(
    draw: ImageDraw.ImageDraw, shoulder: Point, elbow: Point, hand: Point, salt: float
) -> None:
    sx, sy = shoulder
    ex, ey = elbow
    hx, hy = hand
    draw.line([_pt(sx, sy), _pt(ex, ey), _pt(hx, hy)], fill=_rgba(SKIN), width=_s(3.4), joint="curve")
    draw.line([_pt(sx, sy), _pt(ex, ey), _pt(hx, hy)], fill=_rgba(INK), width=_s(0.9), joint="curve")
    # Crude little hand (white glove-ish blob).
    _poly(draw, _blob(hx, hy, 3.4, 3.0, salt, amp=0.8, n=10), _rgba(EYE), _rgba(INK), 1.4)


def _draw_head_spikes(draw: ImageDraw.ImageDraw, hx: float, hy: float, tr: float, salt: float) -> None:
    """Three thick, longish head spikes sweeping back off the small head.
    Facing right, so they point back-left. `tr` trails them out on a lean."""
    spikes = [
        [(hx - 3, hy - 9), (hx - 14, hy - 12), (hx - 26 - tr, hy - 11), (hx - 15, hy - 3), (hx - 2, hy - 3)],
        [(hx - 5, hy - 1), (hx - 16, hy - 1), (hx - 28 - tr, hy + 3), (hx - 15, hy + 6), (hx - 4, hy + 4)],
        [(hx - 4, hy + 5), (hx - 13, hy + 8), (hx - 22 - tr, hy + 12), (hx - 12, hy + 12), (hx - 3, hy + 9)],
    ]
    for i, q in enumerate(spikes):
        _poly(draw, _wobble(q, 2.4, salt + i * 3), _rgba(BLUE_DK), _rgba(INK), 2.6)


def _draw_back_spike(draw: ImageDraw.ImageDraw, rx: float, ry: float, tr: float, salt: float) -> None:
    """The one big weird spike off the MIDDLE OF THE BACK — huge, thick, long,
    sweeping back-left and up. `(rx, ry)` is its root on the torso's back;
    `tr` trails the tip out further on a lean."""
    spike = [
        (rx + 3, ry - 10),
        (rx - 15, ry - 15),
        (rx - 32 - tr, ry - 14),
        (rx - 44 - tr, ry - 8),   # long tip, swept up-back
        (rx - 30 - tr, ry + 3),
        (rx - 13, ry + 7),
        (rx + 3, ry + 6),
    ]
    _poly(draw, _wobble(spike, 3.0, salt), _rgba(BLUE_DK), _rgba(INK), 2.8)


def _draw_leg(
    draw: ImageDraw.ImageDraw, hip: Point, ankle: Point, shade: str, salt: float, bend: float = 0.0
) -> None:
    """One long, awful, spindly leg: a thin wobbly two-segment line with a
    knobbly kicked-out knee."""
    hpx, hpy = hip
    apx, apy = ankle
    kx = (hpx + apx) / 2.0 + bend
    ky = (hpy + apy) / 2.0 + 1.0
    pts = _wobble([hip, (kx, ky), ankle], 1.6, salt)
    scaled = [_pt(x, y) for x, y in pts]
    draw.line(scaled, fill=_rgba(shade), width=_s(2.6), joint="curve")
    draw.line(scaled, fill=_rgba(INK), width=_s(0.8), joint="curve")
    # Knobbly knee joint.
    _poly(draw, _blob(kx, ky, 2.2, 2.2, salt + 1, amp=0.6, n=8), _rgba(shade), _rgba(INK), 1.0)


def _draw_spin_ball(
    img: Image.Image, draw: ImageDraw.ImageDraw, cx: float, cy: float, spin: float, salt: float
) -> None:
    """Sanic's signature spin — a blurry blue ball with quills poking out and
    a red streak wrapping around it. Used by dash/slash."""
    _draw_speed_lines(img, cx, cy, spin, 1.0)
    # Radiating quill spikes around the ball.
    for k in range(6):
        ang = spin * 1.3 + k * math.tau / 6.0
        r0, r1 = 15.0, 24.0
        base_ang = 0.32
        tip = (cx + math.cos(ang) * r1, cy + math.sin(ang) * r1)
        b1 = (cx + math.cos(ang - base_ang) * r0, cy + math.sin(ang - base_ang) * r0)
        b2 = (cx + math.cos(ang + base_ang) * r0, cy + math.sin(ang + base_ang) * r0)
        _poly(draw, _wobble([b1, tip, b2], 1.0, salt + k), _rgba(BLUE_DK), _rgba(INK), 1.4)
    # The ball body.
    _poly(draw, _blob(cx, cy, 16.0, 16.0, salt, amp=2.2, n=20), _rgba(BLUE), _rgba(INK), 2.4)
    # Red motion streak wrapping the ball.
    streak = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(streak, "RGBA")
    sd.arc(_box(cx - 15, cy - 15, cx + 15, cy + 15), int(math.degrees(spin) % 360), int(math.degrees(spin) % 360) + 210, fill=_rgba(SHOE, 210), width=_s(3.2))
    img.alpha_composite(streak)
    # A couple of shoe smudges caught mid-spin.
    for k in range(2):
        ang = spin * 1.3 + k * math.pi
        px, py = cx + math.cos(ang) * 9.0, cy + math.sin(ang) * 9.0
        _poly(draw, _blob(px, py, 4.5, 3.0, salt + k, amp=0.8, n=10), _rgba(SHOE), _rgba(INK), 1.2)


def _draw_face(
    draw: ImageDraw.ImageDraw,
    hx: float,
    hy: float,
    salt: float,
    look: float,
    mouth: str,
) -> None:
    """The derp face on a small head: two beady, close-set, mostly-pupil eyes
    with the fat nose wedged *between* them, and a crude grin. `look` shifts
    the pupils (-1 back .. +1 forward); `mouth` picks an expression."""
    # Muzzle — small peach lobe front-and-under the eyes.
    _poly(draw, _blob(hx + 7.0, hy + 6.0, 9.0, 8.0, salt + 5, amp=1.4, n=18), _rgba(SKIN), _rgba(INK), 2.0)

    # Beady eyes — small, close-set, slightly mismatched.
    lx, ly, lr = hx + 2.5, hy - 3.0, 3.8
    rx, ry, rr = hx + 8.5, hy - 4.0, 3.3
    _poly(draw, _blob(lx, ly, lr, lr, salt + 1, amp=0.6, n=12), _rgba(EYE), _rgba(INK), 1.6)
    _poly(draw, _blob(rx, ry, rr, rr, salt + 2, amp=0.6, n=12), _rgba(EYE), _rgba(INK), 1.6)

    # Fat black nose wedged into the junction *between* the two eyes.
    _poly(draw, _blob(hx + 5.2, hy - 1.0, 3.0, 2.8, salt + 9, amp=0.7, n=12), _rgba(NOSE), None)

    if mouth == "dead":
        # X'd-out eyes.
        for (ex, ey, er) in ((lx, ly, lr), (rx, ry, rr)):
            draw.line(_box(ex - er, ey - er, ex + er, ey + er), fill=_rgba(INK), width=_s(1.4))
            draw.line(_box(ex - er, ey + er, ex + er, ey - er), fill=_rgba(INK), width=_s(1.4))
    else:
        # Beady pupils fill most of each eye; nudge by `look`, tiny glint.
        pdx = look * 1.2
        draw.ellipse(_box(lx - 2.0 + pdx, ly - 2.0, lx + 2.0 + pdx, ly + 2.0), fill=_rgba(INK))
        draw.ellipse(_box(rx - 1.8 + pdx, ry - 1.8, rx + 1.8 + pdx, ry + 1.8), fill=_rgba(INK))
        draw.ellipse(_box(lx - 1.2 + pdx, ly - 1.2, lx - 0.2 + pdx, ly - 0.2), fill=_rgba(EYE))

    # Mouth on the muzzle below the nose.
    if mouth == "grin":
        draw.arc(_box(hx + 1.0, hy + 4.0, hx + 14.0, hy + 13.0), 10, 150, fill=_rgba(INK), width=_s(1.6))
    elif mouth == "open":
        _poly(draw, _wobble([(hx + 3.0, hy + 7.0), (hx + 12.0, hy + 6.0), (hx + 11.0, hy + 12.0), (hx + 4.0, hy + 12.0)], 0.8, salt), _rgba("#7a2b2b"), _rgba(INK), 1.2)
    elif mouth == "hurt":
        draw.arc(_box(hx + 2.0, hy + 8.0, hx + 13.0, hy + 15.0), 190, 350, fill=_rgba(INK), width=_s(1.6))
    else:  # flat little smirk
        draw.line(_box(hx + 2.5, hy + 9.0, hx + 11.0, hy + 8.0), fill=_rgba(INK), width=_s(1.4))


def _draw_sanic(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, "RGBA")

    t = frame_idx / max(1, nframes)
    cyc = math.tau * t
    salt = float(frame_idx + 1)

    # Ground reference: shoes plant near y=112 so the body has headroom.
    # base_x sits right-of-centre to leave room for the long back spikes.
    base_x = 60.0
    ground_y = 112.0

    # ---- Spin-ball anims short-circuit (dash / slash) ----
    if anim in ("dash", "slash"):
        lean = 6.0 if anim == "slash" else 0.0
        ball_cx = base_x + 6.0 + (4.0 if anim == "slash" else 0.0)
        ball_cy = ground_y - 20.0
        spin = cyc * (3.0 if anim == "dash" else 2.4)
        _draw_spin_ball(img, draw, ball_cx + lean, ball_cy, spin, salt)
        return _downsample(img)

    # ---- Pose parameters per anim ----
    bob = 0.0
    lean = 0.0          # forward tilt of head/body (px shift of head vs feet)
    arm_swing = 0.0
    step = 0.0          # leg stride phase
    look = 0.4          # pupil bias (forward-ish by default)
    mouth = "smirk"
    run_blur = False
    airborne = False
    fell = False

    if anim == "idle":
        bob = math.sin(cyc) * 1.6
        arm_swing = math.sin(cyc) * 2.0
        look = 0.2 + math.sin(cyc * 0.5) * 0.3
        mouth = "smirk"
    elif anim == "walk":
        bob = abs(math.sin(cyc)) * 2.2
        step = math.sin(cyc)
        arm_swing = math.sin(cyc) * 7.0
        look = 0.5
    elif anim == "run":
        bob = abs(math.sin(cyc * 2)) * 1.6
        lean = 9.0
        arm_swing = math.sin(cyc * 2) * 9.0
        run_blur = True
        look = 0.9
        mouth = "grin"
    elif anim == "jump":
        bob = -6.0
        lean = 4.0
        arm_swing = -8.0
        airborne = True
        look = 0.6
        mouth = "open"
    elif anim == "fall":
        bob = 2.0 + math.sin(cyc) * 1.0
        lean = -3.0
        arm_swing = 9.0
        airborne = True
        look = -0.2
        mouth = "hurt"
    elif anim == "hit":
        bob = math.sin(cyc * 3) * 2.0
        lean = -6.0
        arm_swing = 11.0
        look = -0.6
        mouth = "hurt"
    elif anim == "death":
        prog = min(1.0, t * 1.4)
        bob = prog * 6.0
        lean = -14.0 * prog
        arm_swing = 12.0
        look = 0.0
        mouth = "dead"
        fell = prog > 0.55
    elif anim == "celebrate":
        bob = math.sin(cyc * 2) * 2.6
        arm_swing = -10.0  # thumbs-up-ish, arm raised
        look = 0.8
        mouth = "grin"

    # Feet/leg root and head placement (head leans forward by `lean`). Hips
    # sit high above the ground so the legs come out long and gangly.
    hips_x = base_x
    hips_y = ground_y - 42.0 + bob
    head_cx = hips_x + 4.0 + lean
    # Head sits up high on a neck, separated from the body.
    head_cy = hips_y - 44.0 + bob * 0.4

    if fell:
        # Toppled over — rotate the whole layout onto its back-ish. Cheap:
        # push head down beside the hips and splay the shoes up.
        head_cx = hips_x - 16.0
        head_cy = hips_y + 6.0

    if run_blur:
        _draw_speed_lines(img, head_cx, head_cy + 6.0, cyc, 1.0)

    # ---- Legs + shoes (behind body) ----
    if run_blur:
        # Classic gotta-go-fast: the long legs dissolve into a red figure-8
        # blur down below the hips.
        blur = Image.new("RGBA", img.size, (0, 0, 0, 0))
        bd = ImageDraw.Draw(blur, "RGBA")
        bcx, bcy = hips_x + 2.0, ground_y - 8.0
        bd.ellipse(_box(bcx - 15, bcy - 14, bcx + 15, bcy + 12), fill=_rgba(SHOE, 150))
        bd.ellipse(_box(bcx - 11, bcy - 18, bcx + 11, bcy + 16), fill=_rgba(SHOE, 110))
        img.alpha_composite(blur)
        for k in range(3):
            ang = cyc * 3.0 + k * math.tau / 3.0
            sxp = bcx + math.cos(ang) * 12.0
            syp = bcy + math.sin(ang) * 11.0
            _draw_shoe(draw, sxp, syp, salt + k, tilt=math.sin(ang) * 2.0)
    elif airborne:
        # Long legs tucked forward (higher on a jump).
        tuck = 8.0 if anim == "jump" else 0.0
        for i, dx in enumerate((-1.0, 9.0)):
            ankle = (hips_x + dx, ground_y - 8.0 - tuck)
            _draw_leg(draw, (hips_x + i * 3.0, hips_y + 4.0), ankle, SKIN if i else SKIN_DK, salt + i, bend=4.0)
            _draw_shoe(draw, ankle[0] + 2.0, ankle[1], salt + i, tilt=-2.0)
    elif fell:
        # Toppled — the long legs splay up and out.
        for i, (dx, dy) in enumerate(((14.0, -4.0), (20.0, -12.0))):
            ankle = (hips_x + dx, hips_y + dy)
            _draw_leg(draw, (hips_x + 2.0, hips_y + 2.0), ankle, SKIN if i else SKIN_DK, salt + i, bend=6.0)
            _draw_shoe(draw, ankle[0] + 3.0, ankle[1], salt + i, tilt=6.0)
    else:
        # Two long spindly legs, front one strides with `step`.
        back_ankle = (hips_x - 3.0 - step * 6.0, ground_y - 4.0)
        front_ankle = (hips_x + 7.0 + step * 7.0, ground_y - 4.0)
        _draw_leg(draw, (hips_x - 1.0, hips_y + 5.0), back_ankle, SKIN_DK, salt, bend=-3.0 - step * 4.0)
        _draw_leg(draw, (hips_x + 3.0, hips_y + 5.0), front_ankle, SKIN, salt + 3, bend=2.0 + step * 4.0)
        _draw_shoe(draw, back_ankle[0] + 2.0, back_ankle[1], salt, tilt=-step * 2.0)
        _draw_shoe(draw, front_ankle[0] + 2.0, front_ankle[1], salt + 3, tilt=step * 2.0)

    # ---- Back arm (behind body) ----
    _draw_arm(
        draw,
        (hips_x + 2.0, hips_y - 6.0),
        (hips_x - 6.0, hips_y - 2.0 - arm_swing * 0.4),
        (hips_x - 12.0, hips_y + 2.0 - arm_swing),
        salt + 7,
    )

    # Torso placement (deliberately bigger than the head — Sanic is a
    # small-headed, big-bodied gremlin).
    tr = lean * 0.5  # trailing extension of the spikes when leaning
    torso_cx = hips_x + 1.0 + lean * 0.3
    torso_cy = hips_y - 6.0

    # ---- The one BIG weird spike — off the MIDDLE OF THE BACK, behind the
    # torso (NOT the head).
    _draw_back_spike(draw, torso_cx - 8.0, torso_cy - 4.0, tr, salt + 4)

    # ---- Neck (connects the separated head to the body) ----
    if not fell:
        neck_top = (head_cx - 1.0, head_cy + 9.0)
        neck_bot = (torso_cx + 1.0, torso_cy - 14.0)
        neck = [
            (neck_top[0] - 6.0, neck_top[1]),
            (neck_top[0] + 6.0, neck_top[1]),
            (neck_bot[0] + 9.0, neck_bot[1]),
            (neck_bot[0] - 9.0, neck_bot[1]),
        ]
        _poly(draw, _wobble(neck, 1.0, salt + 12), _rgba(BLUE), _rgba(INK), 2.0)

    # ---- Torso ----
    torso = _blob(torso_cx, torso_cy, 17.0, 18.0, salt + 6, amp=2.0, n=20)
    _poly(draw, torso, _rgba(BLUE), _rgba(INK), 2.4)
    # Tiny peach chest circle on the belly (low enough to peek out below the
    # front arm).
    _poly(draw, _blob(torso_cx + 4.0, torso_cy + 4.0, 6.0, 6.5, salt + 11, amp=1.0, n=14), _rgba(SKIN), _rgba(INK), 1.4)

    # ---- Head spikes (behind the small head) — thick and longish ----
    _draw_head_spikes(draw, head_cx, head_cy, tr, salt + 4)

    # ---- Head (small lumpy blue blob — smaller than the torso) ----
    _poly(draw, _blob(head_cx, head_cy, 14.0, 13.0, salt, amp=1.8, n=20), _rgba(BLUE), _rgba(INK), 2.4)

    # ---- Face ----
    _draw_face(draw, head_cx, head_cy, salt, look, mouth)

    # ---- Front arm (over body) ----
    if anim == "celebrate":
        # Raised smug thumbs-up.
        _draw_arm(draw, (hips_x + 6.0, hips_y - 8.0), (hips_x + 14.0, hips_y - 18.0), (hips_x + 20.0, hips_y - 30.0), salt + 8)
    else:
        _draw_arm(
            draw,
            (hips_x + 6.0, hips_y - 6.0),
            (hips_x + 14.0, hips_y - 2.0 + arm_swing * 0.4),
            (hips_x + 20.0, hips_y + 2.0 + arm_swing),
            salt + 8,
        )

    return _downsample(img)


def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    return _draw_sanic(animation, frame_idx, nframes)


def render(out_dir: str | Path, **opts) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        label_width=110,
        actor_metadata=ACTOR_METADATA,
    )
    return [
        outputs["canonical"],
        outputs["canonical_transparent"],
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["ron"],
        outputs["actor"],
        outputs["preview"],
    ]
