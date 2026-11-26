"""The King Cobra of the History dimension: the great snake of the forests of Angkor.

The king cobra (Ophiophagus hannah) is the longest venomous snake in the
world. It lives in the forests and the paddy fields of India and of
Southeast Asia, and it eats other snakes. It is olive-brown, with pale
cross-bands on its back and a pale yellow throat; its tail is darker. Its
head is large and round, with large scales on top. When it is alarmed it
lifts the front third of its body high off the ground and spreads its
hood. The hood of the king cobra is long and narrow, not round like the
hood of other cobras. The people of Angkor carved the naga, a great snake
with a spread hood, on the walls and the bridges of their temples.

It rests in a coil with its hood partly open. When it notices a target, it
rises and spreads the hood. It folds its neck back to wind up, strikes with
open jaws, and draws back into the coil.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Sequence, Tuple

from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box
from . import _art_cast_kit as K
from . import _history_africa_kit as H

TARGET_NAME = "king_cobra"
FRAME_SIZE = (160, 144)
WINDUP_S, ACTIVE_S, RECOVERY_S = .55, .15, .60
TOTAL_S = WINDUP_S + ACTIVE_S + RECOVERY_S
ROWS = [("idle", 8, 120), ("walk", 12, 75), ("notice", 8, 85),
        ("windup", 8, 85), ("attack_side", 26, 50), ("hit", 6, 70), ("death", 12, 90)]
MARGIN = 6.0
GROUND = 132.0
# The body is the resting coil and raised neck. The tail, open hood, and
# extended jaws do not change the scale of the same creature.
BODY_BOX = (30, 37, 108, int(GROUND)+1)

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "King Cobra", "Serpentine", "Standard", "Medium", "Walk", ["snake", "cobra", "hood", "strike"],
    "The king cobra of the History dimension's room of Angkor: a long olive-brown snake with pale cross-bands, a large "
    "head and a long hood with a pale barred throat. It rests in a coil with the hood partly open. It spreads the hood "
    "and draws its head back before it bites.",
)
ACTOR_METADATA["tags"] = ["enemy", "history", "angkor"]

HIDE = (91, 104, 60, 255)
HIDE_SHADE = (51, 63, 46, 255)
HIDE_LIGHT = (151, 154, 94, 255)
TAIL = (47, 52, 38, 255)
BAND = (207, 185, 112, 255)
BELLY = (243, 216, 140, 255)
THROAT_BAR = (84, 67, 44, 255)
MOUTH = (150, 63, 63, 255)
FANG = (246, 240, 220, 255)
TONGUE = (40, 30, 32, 255)
EYE = (40, 28, 18, 255)
DUST = (196, 176, 140, 255)

#: The width of the body at its thickest, in px.
BODY_W = 13.0
#: The scale of the head. The head of a king cobra is large.
HEAD = 1.39

Point = Tuple[float, float]

# The poses of the spine: points from the tip of the tail to the back of the
# head. Each pose has the same number of points, so that a row can go from
# one pose to the next. The last number is the angle of the head (degrees,
# down is plus).
COIL = [(24,118), (37,111), (57,111), (78,113), (96,119), (92,124), (70,125), (52,123), (48,116)]
READY = (COIL + [(57,104), (65,89), (64,73), (59,60), (62,48), (70,41)], 2.0)
REARED = (COIL + [(55,101), (66,85), (65,67), (62,52), (64,39), (69,31)], 5.0)
RECOIL = (COIL + [(54,101), (62,85), (57,67), (51,54), (55,41), (62,35)], -13.0)
CRUISE = ([(10,118),(23,121),(35,118),(49,111),(69,111),(85,119),(75,125),(62,123),(55,114),
           (59,102),(72,92),(82,81),(88,70),(95,63),(103,62)], 8.0)
STRIKE = (COIL + [(62,111), (76,102), (88,86), (101,71), (114,63), (127,67)], 19.0)
DEAD = (COIL + [(56,115), (65,119), (76,124), (91,125), (104,125), (116,125)], 2.0)


def _blend(a, b, k: float):
    """The pose `k` of the way from pose `a` to pose `b`."""
    pts = [(xa + (xb - xa) * k, ya + (yb - ya) * k) for (xa, ya), (xb, yb) in zip(a[0], b[0])]
    return pts, a[1] + (b[1] - a[1]) * k


def _smooth(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)


def _spine(ctrl: Sequence[Point], step: float = 1.0) -> List[Point]:
    """A smooth line through the points `ctrl`, with its points at equal steps
    along it."""
    c = [ctrl[0]] + list(ctrl) + [ctrl[-1]]
    dense: List[Point] = []
    for k in range(1, len(c) - 2):
        p0, p1, p2, p3 = c[k - 1], c[k], c[k + 1], c[k + 2]
        for j in range(10):
            u = j / 10.0
            u2, u3 = u * u, u * u * u
            dense.append(tuple(0.5 * (2 * p1[d] + (-p0[d] + p2[d]) * u + (2 * p0[d] - 5 * p1[d] + 4 * p2[d] - p3[d]) * u2
                                      + (-p0[d] + 3 * p1[d] - 3 * p2[d] + p3[d]) * u3) for d in (0, 1)))
    dense.append(ctrl[-1])
    out = [dense[0]]
    left = step
    for (x0, y0), (x1, y1) in zip(dense, dense[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        pos = 0.0
        while seg - pos >= left:
            pos += left
            out.append((x0 + (x1 - x0) * pos / seg, y0 + (y1 - y0) * pos / seg))
            left = step
        left -= seg - pos
    if math.hypot(out[-1][0] - dense[-1][0], out[-1][1] - dense[-1][1]) > 0.2:
        out.append(dense[-1])
    return out


def _normals(pts: Sequence[Point]) -> List[Point]:
    """At each point, the unit normal on the belly side of the line. The line
    goes from the tail to the head, so the normal points down on the ground
    and forward on the reared neck."""
    out = []
    for k in range(len(pts)):
        (x0, y0), (x1, y1) = pts[max(0, k - 1)], pts[min(len(pts) - 1, k + 1)]
        tx, ty = x1 - x0, y1 - y0
        r = math.hypot(tx, ty) or 1.0
        out.append((-ty / r, tx / r))
    return out


def _strip(f: K.Frame, pts, nrm, widths, offset: float, scale: float, colour, body: bool, start: int = 0, stop: int = -1) -> None:
    """A band along the spine: `offset` and `scale` are parts of the width of
    the body there. It is drawn as short thick lines with round ends."""
    stop = len(pts) - 1 if stop < 0 else stop
    for k in range(start, stop, 2):
        j = min(stop, k + 2)
        a = (pts[k][0] + nrm[k][0] * widths[k] * offset, pts[k][1] + nrm[k][1] * widths[k] * offset)
        b = (pts[j][0] + nrm[j][0] * widths[j] * offset, pts[j][1] + nrm[j][1] * widths[j] * offset)
        w = 0.5 * (widths[k] + widths[j]) * scale
        f.limb([a, b], w, colour(k) if callable(colour) else colour, body=body)


def _mix(a, b, k: float):
    k = max(0.0, min(1.0, k))
    return tuple(int(a[c] + (b[c] - a[c]) * k) for c in range(3)) + (255,)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    pose = READY
    hood, gape, tongue, eyes = .72, 0.0, 0.0, "open"
    hump, sway, fade, snap, speed = 0.0, 0.0, 1.0, False, 0.0
    if anim == "idle":
        sway = math.sin(cyc)*.65
        hood += .03*math.sin(cyc)
        tongue = 1.0 if i in (4,5) else 0.0
    elif anim == "walk":
        pose = CRUISE
        hood = .43
        hump = 1.0
        sway = .65*math.sin(2*cyc)
    elif anim == "notice":
        # The held notice pose rises and breathes without folding its hood.
        pose = _blend(READY, REARED, .86+.13*math.sin(cyc))
        hood, eyes = .96+.04*math.sin(cyc), "wide"
        tongue = 1.0 if i in (3,4) else 0.0
    elif anim == "windup":
        pose = _blend(REARED, RECOIL, .84+.1*math.sin(cyc))
        hood, eyes, gape = 1.0, "narrow", 10.0+2.0*math.sin(cyc)
    elif anim == "attack_side":
        time = t*TOTAL_S
        finish = WINDUP_S+ACTIVE_S
        extension = _smooth((time-WINDUP_S)/.085)*(1-_smooth((time-finish)/.29))
        draw_back = _smooth(time/WINDUP_S)*(1-_smooth((time-.82)/.43))
        pose = _blend(_blend(READY, RECOIL, .84*draw_back), STRIKE, extension)
        close = _smooth((time-.67)/.075)
        gape = (10*draw_back + 34*extension)*(1-close)
        hood, eyes = .72+.28*draw_back-.17*extension, "narrow"
        snap, speed = .69 < time < .76, extension
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        pose = _blend(READY, RECOIL, k)
        hood, eyes, gape = .76-.25*k, "shut", 11.0*k
    elif anim == "death":
        sink = _smooth(min(1.0, t * 1.4))
        pose = _blend(READY, DEAD, sink)
        hood, eyes, gape = 1.0 - sink, "shut", 8.0 * sink
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    ctrl, head_angle = pose
    if sway:
        # The sway moves the reared neck, more at the top than at the bottom.
        ctrl = [(x + sway*2.6*max(0.0,(k-8)/6.0), y) for k, (x,y) in enumerate(ctrl)]
    pts = _spine(ctrl)
    total = len(pts) - 1
    if hump:
        # The wave: humps go back along the body; there is none at the tip
        # of the tail and none at the head.
        moved = []
        for k, (x, y) in enumerate(pts):
            s = float(k)
            w = _smooth(s / 18.0) * _smooth((total - 8.0 - s) / 20.0)
            moved.append((x, y - 5.0 * w * (0.5 - 0.5 * math.cos(math.tau * (s / 32.0 + t)))))
        pts = moved
    nrm = _normals(pts)

    def width(k: int) -> float:
        u = k / max(1.0, total)
        w = BODY_W * (0.2 + 0.8 * _smooth(u / 0.4))
        return w * (1.0 - 0.14 * _smooth((u - 0.82) / 0.12))

    widths = [width(k) for k in range(len(pts))]
    neck_k = max(0, total - 34)

    def hide(k: int):
        # The tail is darker than the body.
        return _mix(TAIL, HIDE, _smooth((k / max(1.0, total) - 0.05) / 0.35))

    # The body, then the shade on its belly side and a light line down its
    # back.
    _strip(f, pts, nrm, widths, 0.0, 1.0, hide, True)
    _strip(f, pts, nrm, widths, 0.26, 0.48, HIDE_SHADE, False)
    _strip(f, pts, nrm, widths, -0.28, 0.2, HIDE_LIGHT, False, start=int(total * 0.2))
    # The pale cross-bands: thin, and they lean back like a chevron. They go
    # down from the back to the middle of the side.
    s = 10.0
    while s < neck_k:
        k = int(s)
        (x, y), (nx, ny), w = pts[k], nrm[k], widths[k]
        tx, ty = ny, -nx
        f.ink([(x - nx * w * 0.44 - tx * 2.2, y - ny * w * 0.44 - ty * 2.2), (x + nx * w * 0.12, y + ny * w * 0.12)],
              max(1.0, 0.15 * w), BAND)
        s += 10.0

    # The hood: long and narrow, it spreads out at the two sides of the neck.
    # The back half is olive with a dark edge; the front half is the pale
    # throat with two dark bars across it.
    if hood > 0.05:
        a, b = max(0,total-52), total-2
        back, front = [], []
        for k in range(a, b + 1):
            u = (k - a) / float(b - a)
            # The flare has long sides and rounded shoulders below the head.
            shape = _smooth(u/.52) if u < .52 else 1.0-.66*_smooth((u-.70)/.30)
            hw = widths[k]*.5 + hood*18.5*shape
            (x, y), (nx, ny) = pts[k], nrm[k]
            back.append((x-nx*hw*.92,y-ny*hw*.92))
            front.append((x+nx*hw*1.20,y+ny*hw*1.20))
        mid = pts[a:b + 1]
        f.poly(back + front[::-1], HIDE)
        def panel(edge, fraction):
            return [(x+(ex-x)*fraction,y+(ey-y)*fraction) for (x,y),(ex,ey) in zip(mid,edge)]
        f.poly(back + panel(back,.72)[::-1],HIDE_SHADE,body=False)
        f.ink(panel(back,.63)[7:-3],1.4,BAND)
        far_throat, near_throat = panel(back,.16), panel(front,.85)
        f.poly(far_throat + near_throat[::-1], BELLY, body=False)
        f.poly(panel(front,.49) + near_throat[::-1], _mix(BELLY, BAND, .62), body=False)
        f.ink(panel(front,.93)[8:-3],1.3,HIDE_LIGHT)
        if hood > .32:
            for u in (.34,.52,.70):
                k = int(u*(b-a))
                bend = mid[min(k+3,len(mid)-1)]
                f.ink([far_throat[k],bend,near_throat[k]],2.35,THROAT_BAR)
            # Short belly scutes continue toward the jaw.
            for k in range(int((b-a)*.76),b-a,4):
                f.ink([mid[k],near_throat[k]],.8,BAND)
    else:
        # The throat is pale when the hood is shut.
        _strip(f, pts, nrm, widths, 0.25, 0.4, BELLY, False, start=total - 22)

    # The head: large and round, on the end of the neck.
    hx, hy = pts[-1]
    ang = head_angle

    def D(p: Sequence[Point]) -> List[Point]:
        """Head points: x goes forward along the head and y goes down."""
        return K.turn([(hx + x * HEAD, hy + y * HEAD) for x, y in p], hx, hy, ang)

    def L(p: Sequence[Point]) -> List[Point]:
        """Points of the lower jaw: turned down about the hinge by the gape."""
        return K.turn(D(p), *D([(1.0, 1.6)])[0], gape)

    if gape > 3.0:
        f.poly(D([(1.0, 1.4), (14.0, 1.4)]) + L([(13.0, 1.6), (1.0, 1.6)]), MOUTH)
    f.poly(L([(-3.0, 1.0), (3.0, 1.4), (13.5, 1.5), (13.0, 3.4), (8.0, 4.6), (2.0, 5.0), (-3.0, 4.8)]), BELLY)
    f.poly(D([(-4.0, -4.6), (2.0, -5.8), (8.0, -5.8), (12.5, -4.4), (15.2, -2.0), (15.8, 0.4), (14.6, 1.8), (3.0, 1.9), (-4.0, 2.2)]), HIDE)
    f.poly(D([(0.0, -4.8), (8.0, -5.0), (12.6, -3.6), (8.0, -3.8)]), HIDE_LIGHT, body=False)
    # The large scales on top of the head, and the line of the mouth.
    f.ink(D([(3.0, -5.6), (4.4, -2.8)]), 0.7, HIDE_SHADE)
    f.ink(D([(-1.4, -5.0), (0.0, -1.8)]), 0.7, HIDE_SHADE)
    f.ink(D([(1.0, 1.7), (14.6, 1.7)]), 0.7, HIDE_SHADE)
    if gape > 8.0:
        # The fangs are short, at the front of the upper jaw.
        for x in (10.5,13.0):
            f.poly(D([(x-1.0,1.5),(x+.6,1.5),(x+.1,4.7),(x-.8,5.5)]), FANG, body=False)
    f.dot(*D([(13.8, -1.0)])[0], 0.6, EYE)
    ex, ey = D([(9.0, -1.8)])[0]
    if eyes == "shut":
        f.ink([(ex - 1.8, ey), (ex + 1.8, ey + 0.3)], 1.0, EYE)
    else:
        r = 1.9 if eyes == "wide" else (1.4 if eyes == "narrow" else 1.6)
        f.ellipse(ex, ey, r+.65, r+.4, (220,174,66,255), body=False)
        f.dot(ex+.35,ey,.9,EYE)
        f.dot(ex-.5,ey-.65,.45,(250,235,189,255))
        if eyes == "narrow":
            f.ink(D([(7.0, -4.0), (11.6, -2.8)]), 1.1, HIDE_SHADE)
    if tongue:
        # The forked tongue flicks out from the front of the mouth.
        base = D([(15.4, 1.0)])[0]
        tip = D([(21.0, 1.2)])[0]
        f.ink([base, tip], 0.9, TONGUE)
        f.ink([tip, D([(23.4, -0.4)])[0]], 0.8, TONGUE)
        f.ink([tip, D([(23.2, 2.8)])[0]], 0.8, TONGUE)

    if speed > 0.1:
        x = min(FRAME_SIZE[0] - MARGIN - 16.0, max(MARGIN + 12.0, pts[int(total * 0.55)][0]))
        H.dust(f, x, GROUND - 1.0, speed * 0.6, f"king cobra dust {anim} {i}", spread=0.8, colour=DUST)
    if snap:
        # The mouth shuts: short lines out from the tip of the snout.
        bx, by = D([(16.5, 0.5)])[0]
        for k in (-1.0, 0.0, 1.0):
            f.ink([(bx + 1.5, by + k * 4.0), (min(FRAME_SIZE[0] - MARGIN - 1.0, bx + 6.0), by + k * 6.5)], 1.3, K.alpha(K.WHITE, 0.95))
    if anim == "death" and t > 0.3:
        H.dust(f, 60.0, GROUND - 1.0, min(1.0, (t - 0.3) * 2.0), f"king cobra death {i}", spread=1.4, colour=DUST)
    return f.finish(outline=H.SEPIA_INK, width=1.7, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    outputs = build_sheet(target=TARGET_NAME, rows=ROWS, render_fn=_render_frame, out_dir=Path(out_dir),
                          frame_size=opts.get("frame_size", FRAME_SIZE), auto_crop=False, actor_metadata=ACTOR_METADATA,
                          body_metrics_fn=lambda width,height: body_metrics_for_box(BODY_BOX,width,height),
                          pose_bodies="authored", animation_key_map={name:name for name,_,_ in ROWS})
    return [outputs[key] for key in ("spritesheet", "yaml", "ron", "actor", "preview", "canonical", "canonical_transparent")]


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
