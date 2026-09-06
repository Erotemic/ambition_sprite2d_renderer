"""The authored swing EFFECT: the ribbon a blade leaves, and the lance a poke throws.

⛔ **this used to live in `devtools/swing_tool.py`, which meant it only ever
reached a PREVIEW.** The review artifacts showed the ribbons; the published
sheet had never carried one, because the target's `render()` draws the rig's
parts and nothing composited the effect on top. Authoring the effect in the
tool that reviews it is not authoring it into the game.

Everything here is pure image work — frames in, frames out — so both the
reviewer and the PUBLISHER can call it, which is the whole point of the move.

Palettes: a tilt and a smash must be told apart at a glance, and size alone does
not do it once both are moving, so the two read as different HEAT as well. Both
stay in the fighter's purple; the smash burns hotter and whiter at the core. A
poke is not a sweep at all and gets a cold lance instead of a ribbon.
"""

from __future__ import annotations

import math

from PIL import Image, ImageFilter

from ..core.draw import blending_draw

#: Summed RGB; nothing on the body reaches this, so it separates blade from
#: anatomy without a mask.
BLADE_LUM = 560
TRAIL_BODY = (140, 86, 220)          # tilt: deeper, cooler violet
TRAIL_CORE = (212, 182, 250)
SMASH_TRAIL_BODY = (202, 92, 248)    # smash: hotter magenta-violet
SMASH_TRAIL_CORE = (255, 238, 255)
POKE_BODY = (150, 208, 255)
POKE_CORE = (240, 252, 255)
#: An unarmed strike has no blade to catch the light, so it is read by what it
#: does to the AIR. A tilt shoves air: pale, thin, quick. A smash burns it, the
#: way a capsule burns coming out of orbit -- a deep red plume behind a white
#: compression edge, and the edge is where it hurts.
WIND_BODY = (206, 226, 240)
WIND_CORE = (255, 255, 255)
#: A capsule coming out of orbit is a WHITE compression cap with a plasma
#: sheath boiling off BEHIND it, going orange then deep red then smoke as it
#: cools. Read outward-to-inward these are the shells of that, and the order
#: matters more than the hues: the eye reads heat as "narrow and bright at the
#: front, wide and dark trailing", not as a wedge of one colour.
#: A gun is read at the MUZZLE, not along a swept arc: the danger leaves the
#: weapon and keeps going, so its shapes are a flash that blooms where the shot
#: left and a lance that runs out past the frame. Cold plasma rather than fire,
#: so a shot never reads as a smash's re-entry heat.
MUZZLE_CORE = (244, 252, 255)
MUZZLE_HOT = (186, 246, 255)
MUZZLE_BODY = (96, 214, 252)
BEAM_CORE = (238, 252, 255)
BEAM_BODY = (72, 196, 240)
BEAM_EDGE = (26, 96, 160)
REENTRY_SMOKE = (72, 22, 26)
REENTRY_OUTER = (172, 38, 14)
REENTRY_MID = (255, 118, 24)
REENTRY_HOT = (255, 196, 72)
REENTRY_CORE = (255, 250, 232)
#: Review-only: neither the hit-volume overlay nor the floor rule reaches a
#: published frame — they answer questions ABOUT the art, they are not the art.
HITBOX = (255, 96, 96)
BG = (30, 26, 32, 255)


def _lerp(a, b, t):
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def blade_axis(image: Image.Image):
    """(base, tip) of the blade in image space, base being the end nearer the body."""
    px = image.load()
    blade, body = [], []
    for y in range(image.height):
        for x in range(image.width):
            pixel = px[x, y]
            if pixel[3] < 40:
                continue
            body.append((x, y))
            if sum(pixel[:3]) > BLADE_LUM:
                blade.append((x, y))
    if len(blade) < 6 or not body:
        return None
    n = len(blade)
    cx = sum(p[0] for p in blade) / n
    cy = sum(p[1] for p in blade) / n
    sxx = syy = sxy = 0.0
    for x, y in blade:
        dx, dy = x - cx, y - cy
        sxx += dx * dx
        syy += dy * dy
        sxy += dx * dy
    theta = 0.5 * math.atan2(2 * sxy, sxx - syy)
    ux, uy = math.cos(theta), math.sin(theta)
    projected = [(((x - cx) * ux + (y - cy) * uy), (x, y)) for x, y in blade]
    lo = min(projected)[1]
    hi = max(projected)[1]
    bx = sum(p[0] for p in body) / len(body)
    by = sum(p[1] for p in body) / len(body)
    near = lambda p: math.hypot(p[0] - bx, p[1] - by)
    return (lo, hi) if near(lo) < near(hi) else (hi, lo)


def body_extent(image: Image.Image):
    """(centre x, centre y, lowest y) of the FIGURE, blade excluded.

    Measured on a RAW frame only: the trail's core is brighter than BLADE_LUM,
    so running this after `draw_trail` would count the ribbon as anatomy.
    """
    px = image.load()
    xs, ys, lowest = [], [], 0
    for y in range(image.height):
        for x in range(image.width):
            pixel = px[x, y]
            if pixel[3] < 40 or sum(pixel[:3]) > BLADE_LUM:
                continue
            xs.append(x)
            ys.append(y)
            lowest = max(lowest, y)
    if not xs:
        return None
    return sum(xs) / len(xs), sum(ys) / len(ys), lowest


def ground_y(images) -> float:
    """Floor level: where the fighter's feet are in her NEUTRAL frame.

    A kneel or a blade driven "all the way to the ground" is a claim about a
    height, and a preview with nothing at that height cannot show whether the
    claim holds -- which is why this ships alongside the rule that checks it.
    """
    extent = body_extent(images[0])
    return float(extent[2]) if extent else float(images[0].height - 1)


def draw_ground(images, y: float, colour=(122, 112, 134)):
    """Overlay the floor rule on every frame, so the GIF carries it too."""
    out = []
    for base in images:
        comp = base.copy()
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        blending_draw(layer).line([(0, y), (base.width, y)], fill=colour + (90,), width=1)
        comp.alpha_composite(layer)
        out.append(comp)
    return out




def draw_trail(images, window: int = 3, subdiv: int = 5, inner: float = 0.58,
               alpha: int = 120, blur: float = 0.8, core_alpha: int = 150, active=None,
               body_rgb=None, core_rgb=None, falloff: float = 1.7, axes=None):
    """`window`/`inner`/`alpha` are what separate a tilt from a smash: a smash
    wants a longer, wider, brighter ribbon so the commitment reads.

    `falloff` is how fast a segment dims with age, and it has to move with
    `window`: stretching the window so the hit volume can grow also stretches
    the fade, and a smash ribbon lengthened without flattening the falloff just
    goes dim -- longer AND fainter, which is the opposite of grander.

    `active` is the SAME frame set the hit volume uses, and that is the point:
    the ribbon and the hitbox describe one swing, so a charge frame that cannot
    hurt anyone must not sweep light either. Segments keep fading for `window`
    frames afterwards, so a recovery still trails off instead of snapping dark.
    """
    live = None if active is None else set(active)
    body_rgb = tuple(body_rgb) if body_rgb else TRAIL_BODY
    core_rgb = tuple(core_rgb) if core_rgb else TRAIL_CORE
    axes = axes if axes is not None else [blade_axis(im) for im in images]
    out = []
    for i, base in enumerate(images):
        trail = Image.new("RGBA", base.size, (0, 0, 0, 0))
        for k in range(window, 0, -1):
            j0, j1 = i - k, i - k + 1
            if j0 < 0 or j1 >= len(images) or axes[j0] is None or axes[j1] is None:
                continue
            if live is not None and (j0 not in live or j1 not in live):
                continue
            for s in range(subdiv):
                t0, t1 = s / subdiv, (s + 1) / subdiv
                age = ((k - 1) + (1 - t1)) / window
                a = int(alpha * (1.0 - age) ** falloff)
                if a <= 2:
                    continue
                b0 = _lerp(axes[j0][0], axes[j1][0], t0)
                p0 = _lerp(axes[j0][1], axes[j1][1], t0)
                b1 = _lerp(axes[j0][0], axes[j1][0], t1)
                p1 = _lerp(axes[j0][1], axes[j1][1], t1)
                f = inner + (1.0 - inner) * 0.55 * age
                seg = Image.new("RGBA", base.size, (0, 0, 0, 0))
                blending_draw(seg).polygon(
                    [_lerp(b0, p0, f), p0, p1, _lerp(b1, p1, f)], fill=body_rgb + (a,)
                )
                trail.alpha_composite(seg)
        trail = trail.filter(ImageFilter.GaussianBlur(blur))
        core_live = live is None or (i in live and i - 1 in live)
        if i > 0 and core_live and axes[i] and axes[i - 1]:
            core = Image.new("RGBA", base.size, (0, 0, 0, 0))
            blending_draw(core).polygon(
                [_lerp(axes[i - 1][0], axes[i - 1][1], 0.80), axes[i - 1][1],
                 axes[i][1], _lerp(axes[i][0], axes[i][1], 0.80)],
                fill=core_rgb + (core_alpha,),
            )
            trail.alpha_composite(core.filter(ImageFilter.GaussianBlur(0.5)))
        # ⛔ TRANSPARENT, not the review backdrop. Filling with `BG` here made
        # every composited frame an opaque rectangle — which is invisible in a
        # preview strip that draws its own dark field behind, and fatal to a
        # PUBLISHED frame: the sheet crops to the union alpha, so an opaque
        # frame is a frame with no silhouette at all. The reviewer lays its own
        # background; the effect is art, not a backdrop.
        comp = Image.new("RGBA", base.size, (0, 0, 0, 0))
        comp.alpha_composite(trail)
        comp.alpha_composite(base)
        out.append(comp)
    return out


# A poke is not a slow sweep -- it is a line. Its light runs ALONG the blade
# instead of trailing behind it, so a thrust reads as reach rather than as arc.


def poke_polygon(axes, i, extend: float = 1.30, width: float = 13.0,
                 waist: float = 0.66, inner: float = 0.10):
    """Lens along the blade axis: the volume a THRUST occupies.

    A swept ribbon says "this arc is dangerous"; a poke has no arc, and drawing
    one for it would promise a sweep the move does not have. So the shape is
    axial -- it starts near the hilt, bulges at `waist` and comes to a point
    past the tip, which is where a thrust's reach actually is.
    """
    if axes[i] is None:
        return None
    base, tip = axes[i]
    dx, dy = tip[0] - base[0], tip[1] - base[1]
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return None
    ux, uy = dx / length, dy / length
    nx, ny = -uy, ux
    start = _lerp(base, tip, inner)
    end = (base[0] + dx * extend, base[1] + dy * extend)
    mid = _lerp(start, end, waist)
    half = width / 2.0
    return [start, (mid[0] + nx * half, mid[1] + ny * half), end,
            (mid[0] - nx * half, mid[1] - ny * half)]


def draw_poke(images, active=None, extend: float = 1.30, width: float = 13.0,
              waist: float = 0.66, inner: float = 0.10, alpha: int = 190,
              blur: float = 1.0, core_alpha: int = 225, falloff: float = 2.2,
              window: int = 2, body_rgb=None, core_rgb=None, axes=None):
    """Draw the thrust flash, fading for `window` frames after each live one."""
    live = None if active is None else set(active)
    body_rgb = tuple(body_rgb) if body_rgb else POKE_BODY
    core_rgb = tuple(core_rgb) if core_rgb else POKE_CORE
    axes = axes if axes is not None else [blade_axis(im) for im in images]
    out = []
    for i, base_im in enumerate(images):
        layer = Image.new("RGBA", base_im.size, (0, 0, 0, 0))
        for k in range(window, -1, -1):
            j = i - k
            if j < 0 or (live is not None and j not in live):
                continue
            poly = poke_polygon(axes, j, extend, width, waist, inner)
            if poly is None:
                continue
            age = k / (window + 1)
            a = int(alpha * (1.0 - age) ** falloff)
            if a <= 2:
                continue
            spike = Image.new("RGBA", base_im.size, (0, 0, 0, 0))
            blending_draw(spike).polygon(poly, fill=body_rgb + (a,))
            layer.alpha_composite(spike)
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
        if live is None or i in live:
            poly = poke_polygon(axes, i, extend, width * 0.34, waist, inner)
            if poly is not None:
                core = Image.new("RGBA", base_im.size, (0, 0, 0, 0))
                blending_draw(core).polygon(poly, fill=core_rgb + (core_alpha,))
                layer.alpha_composite(core.filter(ImageFilter.GaussianBlur(0.5)))
        comp = Image.new("RGBA", base_im.size, (0, 0, 0, 0))
        comp.alpha_composite(layer)
        comp.alpha_composite(base_im)
        out.append(comp)
    return out


# An unarmed sweep: the same travel a ribbon describes, raked into separate
# streaks instead of filled solid. A fist has no edge to leave one bright line,
# and a solid wedge off a fist reads as a weapon the character is not holding.


def draw_wind(images, window: int = 3, subdiv: int = 6, inner: float = 0.34,
              alpha: int = 132, blur: float = 0.7, core_alpha: int = 150,
              active=None, body_rgb=None, core_rgb=None, falloff: float = 2.0,
              streaks: int = 3, spread: float = 0.34, axes=None):
    """Draw a whoosh: a few thin arcs raked along where the limb travelled.

    `streaks` is what separates this from a blade's ribbon. One filled quad says
    "an edge passed through here"; several thin ones at different radii say "air
    moved", which is the honest claim for a punch and still marks the same
    ground the hit volume covers.

    `spread` fans the streaks across the limb's width so the outermost rides the
    knuckles and the innermost stays near the elbow -- a tilt that reads as fast
    without pretending to the reach of a smash.
    """
    live = None if active is None else set(active)
    body_rgb = tuple(body_rgb) if body_rgb else WIND_BODY
    core_rgb = tuple(core_rgb) if core_rgb else WIND_CORE
    axes = axes if axes is not None else [blade_axis(im) for im in images]
    out = []
    for i, base_im in enumerate(images):
        layer = Image.new("RGBA", base_im.size, (0, 0, 0, 0))
        for k in range(window, 0, -1):
            j0, j1 = i - k, i - k + 1
            if j0 < 0 or j1 >= len(images) or axes[j0] is None or axes[j1] is None:
                continue
            if live is not None and (j0 not in live or j1 not in live):
                continue
            for streak in range(streaks):
                # Each streak rides its own radius along the limb, so they fan
                # apart as the arc opens instead of stacking into one wedge.
                far = 1.0 - spread * (streak / max(1, streaks - 1))
                near = far - (1.0 - inner) / (streaks + 1)
                for sub in range(subdiv):
                    t0, t1 = sub / subdiv, (sub + 1) / subdiv
                    age = ((k - 1) + (1 - t1)) / window
                    a = int(alpha * (1.0 - age) ** falloff)
                    if a <= 2:
                        continue
                    b0 = _lerp(axes[j0][0], axes[j1][0], t0)
                    p0 = _lerp(axes[j0][1], axes[j1][1], t0)
                    b1 = _lerp(axes[j0][0], axes[j1][0], t1)
                    p1 = _lerp(axes[j0][1], axes[j1][1], t1)
                    seg = Image.new("RGBA", base_im.size, (0, 0, 0, 0))
                    blending_draw(seg).polygon(
                        [_lerp(b0, p0, near), _lerp(b0, p0, far),
                         _lerp(b1, p1, far), _lerp(b1, p1, near)],
                        fill=body_rgb + (a,),
                    )
                    layer.alpha_composite(seg)
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
        core_live = live is None or (i in live and i - 1 in live)
        if i > 0 and core_live and axes[i] and axes[i - 1]:
            core = Image.new("RGBA", base_im.size, (0, 0, 0, 0))
            blending_draw(core).polygon(
                [_lerp(axes[i - 1][0], axes[i - 1][1], 0.84), axes[i - 1][1],
                 axes[i][1], _lerp(axes[i][0], axes[i][1], 0.84)],
                fill=core_rgb + (core_alpha,),
            )
            layer.alpha_composite(core.filter(ImageFilter.GaussianBlur(0.6)))
        comp = Image.new("RGBA", base_im.size, (0, 0, 0, 0))
        comp.alpha_composite(layer)
        comp.alpha_composite(base_im)
        out.append(comp)
    return out


def strike_travel(axes, i, lookback: int = 3):
    """Where the striking end went, and how far, over the last few frames.

    ⛔ THE LIMB AXIS IS NOT THE DIRECTION OF TRAVEL. For a straight punch the
    two coincide, which is why aligning the plume to the arm looked right on a
    cross and wrong on everything else: a sweeping kick's foot travels roughly
    ACROSS its own shin, so a plume laid along the shin trails off sideways
    from the arc it is supposed to be burning through.

    Returns ``(unit direction, distance)``, or ``(None, 0.0)`` when the strike
    point has not moved yet — a thrust on its first live frame has a direction
    but no history, and the caller falls back to the limb for that one.
    """
    if axes[i] is None:
        return None, 0.0
    point = axes[i][1]
    for step in range(1, lookback + 1):
        previous = i - step
        if previous < 0 or axes[previous] is None:
            continue
        was = axes[previous][1]
        dx, dy = point[0] - was[0], point[1] - was[1]
        distance = math.hypot(dx, dy)
        if distance > 1e-6:
            return (dx / distance, dy / distance), distance
    return None, 0.0


def reentry_polygon(axes, i, spread: float = 1.15, extend: float = 1.12,
                    trail: float = 1.05, scale: float = 1.0):
    """The plume a heavy strike drags, tip first.

    ⛔ POINTED THE WRONG WAY ROUND AT FIRST: apex at the elbow, mouth flaring
    out past the knuckles. That is a megaphone, not a re-entry. A body coming
    through atmosphere leads with a compressed point and trails its glow
    BEHIND — so the tip sits just past the fist, in the direction of travel,
    and the plume opens back along the limb.

    `extend` places that tip beyond the fist (1.0 is on the knuckles), `trail`
    is how far back the plume flares, and `spread` is the mouth width. All three
    are fractions of the LIMB, not pixel constants, so one set of numbers
    describes a punch and a kick and survives a character of another size.

    `scale` shrinks the whole plume toward the TIP for the hotter inner shells:
    layering them concentrically costs one function, and shrinking toward the
    tip is what puts the white where the heat is.
    """
    if axes[i] is None:
        return None
    base, tip = axes[i]
    dx, dy = tip[0] - base[0], tip[1] - base[1]
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return None
    travel, distance = strike_travel(axes, i)
    if travel is None:
        # No history to read: a thrust's first live frame. The limb is the best
        # available guess at where it is going.
        ux, uy = dx / length, dy / length
        reach = length * trail * scale
    else:
        ux, uy = travel
        # The plume is as long as the ground actually covered, floored so a
        # slow frame still burns rather than winking out.
        reach = max(distance * 1.7, length * 0.5) * trail * scale
    nx, ny = -uy, ux
    point = (tip[0] + ux * length * (extend - 1.0),
             tip[1] + uy * length * (extend - 1.0))
    mouth = (point[0] - ux * reach, point[1] - uy * reach)
    half = length * spread * 0.5 * scale
    # Widest a little way behind the shock front, then TAPERING to the tail. A
    # mouth as wide as the belly makes a slab: the shape has to close toward the
    # end or it reads as a lit rectangle dragged behind the fist rather than
    # something burning off.
    belly = _lerp(point, mouth, 0.42)
    tail = half * 0.55
    return [
        point,
        (belly[0] + nx * half, belly[1] + ny * half),
        (mouth[0] + nx * tail, mouth[1] + ny * tail),
        (mouth[0] - nx * tail, mouth[1] - ny * tail),
        (belly[0] - nx * half, belly[1] - ny * half),
    ]


def draw_reentry(images, active=None, spread: float = 1.15, extend: float = 1.12,
                 trail: float = 1.05, alpha: int = 96, blur: float = 1.6,
                 core_alpha: int = 210, window: int = 3, falloff: float = 1.9,
                 shells=None, body_rgb=None, core_rgb=None, axes=None):
    """Draw the atmospheric-entry plume: dim red shell, hot mid, white edge.

    Three nested cones rather than one, because a single flat wedge reads as a
    piece of geometry and a re-entry glow reads as heat: the eye wants the
    colour to climb as the shape narrows. The brightest, narrowest shell sits at
    the mouth, which is exactly where the hit volume claims the damage is.

    Fades for `window` frames after the last live one so the commitment hangs in
    the air, the way a smash's recovery should feel heavy.
    """
    live = None if active is None else set(active)
    shells = shells or [
        (1.00, REENTRY_SMOKE, 0.85),
        (0.86, REENTRY_OUTER, 1.00),
        (0.62, REENTRY_MID, 1.05),
        (0.40, REENTRY_HOT, 1.05),
        (0.22, body_rgb or REENTRY_CORE, 0.95),
    ]
    core_rgb = tuple(core_rgb) if core_rgb else REENTRY_CORE
    axes = axes if axes is not None else [blade_axis(im) for im in images]
    out = []
    for i, base_im in enumerate(images):
        layer = Image.new("RGBA", base_im.size, (0, 0, 0, 0))
        for k in range(window, -1, -1):
            j = i - k
            if j < 0 or (live is not None and j not in live):
                continue
            age = k / (window + 1)
            for index, (scale, rgb, weight) in enumerate(shells):
                a = int(alpha * weight * (1.0 - age) ** falloff)
                if a <= 2:
                    continue
                # Cooler shells linger and swell; the hot core does not. That
                # difference is the whole read: without it every shell fades in
                # lockstep and the plume dims rather than burns out.
                cool = index / max(1, len(shells) - 1)
                poly = reentry_polygon(
                    axes, j, spread * (1.0 + 0.22 * cool * age),
                    extend, trail, scale * (1.0 + 0.3 * cool * age),
                )
                if poly is None:
                    continue
                shell = Image.new("RGBA", base_im.size, (0, 0, 0, 0))
                blending_draw(shell).polygon(poly, fill=tuple(rgb) + (a,))
                layer.alpha_composite(shell)
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
        if live is None or i in live:
            # The compression edge: a thin bright cap across the mouth, the
            # brightest thing in the frame and the front of the hit volume. It
            # gets a bloom under it so the white does not sit on the red like a
            # sticker -- heat has no hard edge on its hot side.
            # The cap rides the TIP now, so both of these are short plumes
            # rather than a slice across a distant mouth.
            bloom = reentry_polygon(axes, i, spread * 0.5, extend, trail * 0.34)
            if bloom is not None:
                halo = Image.new("RGBA", base_im.size, (0, 0, 0, 0))
                blending_draw(halo).polygon(bloom, fill=REENTRY_HOT + (int(core_alpha * 0.5),))
                layer.alpha_composite(halo.filter(ImageFilter.GaussianBlur(2.4)))
            poly = reentry_polygon(axes, i, spread * 0.3, extend, trail * 0.18)
            if poly is not None:
                edge = Image.new("RGBA", base_im.size, (0, 0, 0, 0))
                blending_draw(edge).polygon(poly, fill=core_rgb + (core_alpha,))
                layer.alpha_composite(edge.filter(ImageFilter.GaussianBlur(0.6)))
        comp = Image.new("RGBA", base_im.size, (0, 0, 0, 0))
        comp.alpha_composite(layer)
        comp.alpha_composite(base_im)
        out.append(comp)
    return out


def shot_axis(axes, i, reach: float, spread_deg: float = 0.0):
    """The line a shot travels: from the muzzle, out along the barrel.

    ⛔ A GUN'S DANGER IS NOT ON THE WEAPON. Every other effect here describes
    where a limb or a blade IS; a shot describes where it WENT, which is past
    the end of the barrel and off the screen. So the returned segment starts at
    the muzzle and runs `reach` barrel-lengths beyond it, and the art and the
    hit volume are both built on that rather than on the cannon's own outline.
    """
    if axes[i] is None:
        return None
    breech, muzzle = axes[i]
    dx, dy = muzzle[0] - breech[0], muzzle[1] - breech[1]
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return None
    angle = math.atan2(dy, dx) + math.radians(spread_deg)
    ux, uy = math.cos(angle), math.sin(angle)
    return muzzle, (muzzle[0] + ux * length * reach, muzzle[1] + uy * length * reach), length


def muzzle_polygon(axes, i, reach: float = 1.5, flare: float = 0.55,
                   spread_deg: float = 0.0, scale: float = 1.0):
    """The cone of a discharge: narrow at the muzzle, opening as it leaves."""
    shot = shot_axis(axes, i, reach * scale, spread_deg)
    if shot is None:
        return None
    muzzle, far, length = shot
    ux = (far[0] - muzzle[0]) / max(1e-6, math.dist(muzzle, far))
    uy = (far[1] - muzzle[1]) / max(1e-6, math.dist(muzzle, far))
    nx, ny = -uy, ux
    lip = length * flare * 0.16 * scale
    mouth = length * flare * scale
    return [
        (muzzle[0] + nx * lip, muzzle[1] + ny * lip),
        (far[0] + nx * mouth, far[1] + ny * mouth),
        (far[0] - nx * mouth, far[1] - ny * mouth),
        (muzzle[0] - nx * lip, muzzle[1] - ny * lip),
    ]


def draw_muzzle(images, active=None, reach: float = 1.5, flare: float = 0.55,
                alpha: int = 150, core_alpha: int = 225, blur: float = 1.5,
                window: int = 2, falloff: float = 2.4, spread=None, bloom: float = 1.0,
                body_rgb=None, core_rgb=None, hot_rgb=None, axes=None):
    """Draw the discharge: a bloom on the barrel and a cone of light leaving it.

    `spread` is a list of angle offsets — one cone each — so a flak burst is the
    same function as a single shot rather than a second effect that has to be
    kept in step with it.

    ⛔ ALL THREE SHELLS ARE AUTHORABLE, INCLUDING THE MIDDLE ONE. The defaults are
    a beast's cold plasma; a gunpowder flash is orange and white, and with only
    the outer and core colours exposed the inner shell stayed icy and the
    Officer's service pistol published a discharge the colour of a raygun.
    """
    live = None if active is None else set(active)
    body_rgb = tuple(body_rgb) if body_rgb else MUZZLE_BODY
    core_rgb = tuple(core_rgb) if core_rgb else MUZZLE_CORE
    hot_rgb = tuple(hot_rgb) if hot_rgb else MUZZLE_HOT
    offsets = list(spread) if spread else [0.0]
    axes = axes if axes is not None else [blade_axis(im) for im in images]
    out = []
    for i, base_im in enumerate(images):
        layer = Image.new("RGBA", base_im.size, (0, 0, 0, 0))
        for k in range(window, -1, -1):
            j = i - k
            if j < 0 or (live is not None and j not in live):
                continue
            age = k / (window + 1)
            fade_a = (1.0 - age) ** falloff
            for offset in offsets:
                for shell, rgb, weight in ((1.0, body_rgb, 1.0), (0.5, hot_rgb, 0.9)):
                    a = int(alpha * weight * fade_a)
                    if a <= 2:
                        continue
                    poly = muzzle_polygon(axes, j, reach, flare, offset, shell)
                    if poly is None:
                        continue
                    cone = Image.new("RGBA", base_im.size, (0, 0, 0, 0))
                    blending_draw(cone).polygon(poly, fill=tuple(rgb) + (a,))
                    layer.alpha_composite(cone)
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
        if (live is None or i in live) and axes[i] is not None:
            # The flash ON the barrel: a gun tells you it fired at the weapon,
            # not only downrange, and without this the recoil frame reads as the
            # beast simply pointing.
            muzzle = axes[i][1]
            radius = max(2.0, math.dist(axes[i][0], axes[i][1]) * 0.22 * bloom)
            flash = Image.new("RGBA", base_im.size, (0, 0, 0, 0))
            blending_draw(flash).ellipse(
                [muzzle[0] - radius, muzzle[1] - radius, muzzle[0] + radius, muzzle[1] + radius],
                fill=core_rgb + (core_alpha,),
            )
            layer.alpha_composite(flash.filter(ImageFilter.GaussianBlur(radius * 0.42)))
        comp = Image.new("RGBA", base_im.size, (0, 0, 0, 0))
        comp.alpha_composite(layer)
        comp.alpha_composite(base_im)
        out.append(comp)
    return out


def beam_polygon(axes, i, reach: float = 8.0, width: float = 0.30,
                 spread_deg: float = 0.0, scale: float = 1.0):
    """A parallel-sided lance from the muzzle to well past the frame."""
    shot = shot_axis(axes, i, reach, spread_deg)
    if shot is None:
        return None
    muzzle, far, length = shot
    span = math.dist(muzzle, far)
    ux, uy = (far[0] - muzzle[0]) / span, (far[1] - muzzle[1]) / span
    nx, ny = -uy, ux
    half = length * width * 0.5 * scale
    # Slightly pinched at the muzzle so the beam reads as leaving something.
    return [
        (muzzle[0] + nx * half * 0.55, muzzle[1] + ny * half * 0.55),
        (far[0] + nx * half, far[1] + ny * half),
        (far[0] - nx * half, far[1] - ny * half),
        (muzzle[0] - nx * half * 0.55, muzzle[1] - ny * half * 0.55),
    ]


def draw_beam(images, active=None, reach: float = 8.0, width: float = 0.30,
              alpha: int = 168, core_alpha: int = 240, blur: float = 2.0,
              window: int = 2, falloff: float = 1.6, bloom: float = 1.4,
              body_rgb=None, core_rgb=None, axes=None):
    """Draw a sustained beam: dim edge, bright body, white core, muzzle bloom.

    Layered outward-in like the re-entry plume and for the same reason — a
    single flat bar reads as a drawn rectangle, and light does not have one
    colour. The bloom sits at the muzzle because that is where a player looks to
    know who fired.
    """
    live = None if active is None else set(active)
    body_rgb = tuple(body_rgb) if body_rgb else BEAM_BODY
    core_rgb = tuple(core_rgb) if core_rgb else BEAM_CORE
    axes = axes if axes is not None else [blade_axis(im) for im in images]
    out = []
    for i, base_im in enumerate(images):
        layer = Image.new("RGBA", base_im.size, (0, 0, 0, 0))
        for k in range(window, -1, -1):
            j = i - k
            if j < 0 or (live is not None and j not in live):
                continue
            fade_a = (1.0 - k / (window + 1)) ** falloff
            for shell, rgb, weight in (
                (1.55, BEAM_EDGE, 0.75), (1.0, body_rgb, 1.0), (0.42, core_rgb, 1.0),
            ):
                a = int(alpha * weight * fade_a)
                if a <= 2:
                    continue
                poly = beam_polygon(axes, j, reach, width, 0.0, shell)
                if poly is None:
                    continue
                bar = Image.new("RGBA", base_im.size, (0, 0, 0, 0))
                blending_draw(bar).polygon(poly, fill=tuple(rgb) + (a,))
                layer.alpha_composite(bar)
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
        if (live is None or i in live) and axes[i] is not None:
            muzzle = axes[i][1]
            radius = max(3.0, math.dist(axes[i][0], axes[i][1]) * 0.34 * bloom)
            flash = Image.new("RGBA", base_im.size, (0, 0, 0, 0))
            blending_draw(flash).ellipse(
                [muzzle[0] - radius, muzzle[1] - radius, muzzle[0] + radius, muzzle[1] + radius],
                fill=core_rgb + (core_alpha,),
            )
            layer.alpha_composite(flash.filter(ImageFilter.GaussianBlur(radius * 0.5)))
        comp = Image.new("RGBA", base_im.size, (0, 0, 0, 0))
        comp.alpha_composite(layer)
        comp.alpha_composite(base_im)
        out.append(comp)
    return out


def _hull(points):
    """Convex hull (monotone chain). A hull cannot self-intersect, which the
    raw swept quad can: when the blade crosses over, base and tip swap sides
    and [b0, t0, t1, b1] draws an hourglass instead of a volume."""
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in points))
    if len(pts) < 3:
        return list(pts)
    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2:
                (ax, ay), (bx, by) = out[-2], out[-1]
                if (bx - ax) * (p[1] - ay) - (by - ay) * (p[0] - ax) > 0:
                    break
                out.pop()
            out.append(p)
        return out[:-1]
    return half(pts) + half(reversed(pts))


def hit_polygon(axes, i, reach: float = 1.0, linger: int | None = None, first: int = 0,
                extend: float = 1.0, inflate: float = 0.0):
    """Proposed hit volume for frame `i`: the hull of the blade over the last
    live frames, so the volume GROWS as the swing travels and by the end covers
    the whole ribbon rather than collapsing to one thin swept step. `linger`
    caps that window; without one the volume is everything the blade has swept
    since the move went live, which is what makes the hitbox match the trail.

    The window never reaches back before `first`, the frame the attack goes
    live. Without that clamp a smash's opening hitbox swallowed the overhead
    wind-up and so extended BEHIND the fighter -- a volume covering a position
    the blade held while the move was still inactive.

    `reach` trims the inner end so the volume covers blade rather than fist;
    `extend` pushes the outer end PAST the tip and `inflate` grows the hull
    sideways. A hitbox is not a tracing of the art -- a move that connects only
    where the sprite overlaps feels stingy -- so the generous part is declared
    rather than faked by drawing a longer sword.

    NOTE: derived from the swing, not authored data. No hitboxes exist for this
    character yet (`RigDocument`'s "hitboxes" slot is empty), so this shows the
    reach a hitbox WOULD need. The shipping path is
    `core.slash_envelope.SwingDescriptor`, which drives the hit polygon and the
    effect art off one profile so they cannot drift.
    """
    pts = []
    start = first if linger is None else max(first, i - linger + 1)
    for j in range(start, i + 1):
        if axes[j] is None:
            continue
        base, tip = axes[j]
        if extend != 1.0:
            tip = (base[0] + (tip[0] - base[0]) * extend,
                   base[1] + (tip[1] - base[1]) * extend)
        if reach != 1.0:
            base = _lerp(base, tip, 1.0 - reach)
        pts.extend([base, tip])
    if len(pts) < 3:
        return None
    hull = _hull(pts)
    if inflate > 0.0 and len(hull) >= 3:
        cx = sum(p[0] for p in hull) / len(hull)
        cy = sum(p[1] for p in hull) / len(hull)
        grown = []
        for x, y in hull:
            dx, dy = x - cx, y - cy
            length = math.hypot(dx, dy) or 1.0
            grown.append((x + dx / length * inflate, y + dy / length * inflate))
        hull = grown
    return hull


def hit_windows(hitbox: dict):
    """`active` as a list of WINDOWS, however the spec wrote it.

    A neutral air hits twice, and the second hit must not inherit the first's
    swept volume -- one accumulating hull across both would claim everything
    between them, which is precisely the space the move passes through without
    threatening. So each window starts its own volume.
    """
    active = hitbox.get("active")
    if not active:
        return []
    if isinstance(active[0], (list, tuple)):
        return [sorted(int(f) for f in window) for window in active]
    return [sorted(int(f) for f in active)]


def window_start(windows, i):
    """The frame the volume containing `i` began, or None if `i` is not live."""
    for window in windows:
        if i in window:
            return window[0]
    return None


# ── stage machinery ───────────────────────────────────────────────────────────
#
# Not every authored effect is a swing. A trap door and a flyline are things the
# STAGE does to a character, and they are drawn here for the same reason the
# ribbons are: the reviewer and the PUBLISHER have to call the same code, or the
# sheet ships without them.

TRAP_MOUTH = (14, 11, 16)
TRAP_LIP = (58, 48, 40)
TRAP_LIP_LIT = (104, 88, 70)
TRAP_DUST = (176, 162, 146)
WIRE_BODY = (206, 210, 220)
WIRE_GLINT = (255, 255, 250)


def draw_trapdoor(images, active=None, width: float = 46.0, depth: float = 9.0,
                  lip: float = 4.0, dust: float = 1.0, open_frames: int = 2,
                  mouth_rgb=None, lip_rgb=None, dust_rgb=None, axes=None):
    """A hole in the boards under the character, opening and closing.

    The axis' TIP is the ground point -- the toe of the foot standing on the
    mark -- so the door opens where she is, not where the frame's centre happens
    to be.

    ⛔ THE HOLE IS DRAWN BEHIND HER AND THE LIP IN FRONT. A door composited
    wholly on top puts a black bar across her shins on the way down; wholly
    behind, the near edge vanishes and she reads as standing in a shadow. The
    mouth goes under, the near lip goes over, and the two together read as a
    board she is passing through.
    """
    live = None if active is None else set(active)
    mouth = tuple(mouth_rgb) if mouth_rgb else TRAP_MOUTH
    lip_c = tuple(lip_rgb) if lip_rgb else TRAP_LIP
    dust_c = tuple(dust_rgb) if dust_rgb else TRAP_DUST
    axes = axes if axes is not None else [blade_axis(im) for im in images]
    anchor = next((a[1] for i, a in enumerate(axes)
                   if a is not None and (live is None or i in live)), None)
    out = []
    for i, base in enumerate(images):
        if anchor is None or (live is not None and i not in live):
            out.append(base.copy())
            continue
        first = min(live) if live else 0
        age = i - first
        # The door swings open over `open_frames` and stays open.
        span = min(1.0, (age + 1) / max(1, open_frames))
        half = width * 0.5 * span
        cx, cy = anchor
        under = Image.new("RGBA", base.size, (0, 0, 0, 0))
        over = Image.new("RGBA", base.size, (0, 0, 0, 0))
        blending_draw(under).polygon(
            [(cx - half, cy - depth * 0.35), (cx + half, cy - depth * 0.35),
             (cx + half * 0.86, cy + depth), (cx - half * 0.86, cy + depth)],
            fill=mouth + (246,))
        # Far lip, behind her; near lip, in front.
        blending_draw(under).polygon(
            [(cx - half, cy - depth * 0.35 - lip), (cx + half, cy - depth * 0.35 - lip),
             (cx + half, cy - depth * 0.35), (cx - half, cy - depth * 0.35)],
            fill=TRAP_LIP_LIT + (232,))
        blending_draw(over).polygon(
            [(cx - half * 0.86, cy + depth), (cx + half * 0.86, cy + depth),
             (cx + half * 0.86, cy + depth + lip), (cx - half * 0.86, cy + depth + lip)],
            fill=lip_c + (250,))
        if dust > 0.0 and age <= open_frames + 1:
            fade = int(150 * dust * (1.0 - age / (open_frames + 2)))
            if fade > 3:
                puff = Image.new("RGBA", base.size, (0, 0, 0, 0))
                for k in range(5):
                    t = (k - 2) / 2.0
                    r = (5.0 + 3.5 * abs(t)) * dust
                    px = cx + t * half * 0.8
                    py = cy - depth * 0.4 - 3.0 * (1.0 - abs(t))
                    blending_draw(puff).ellipse(
                        [px - r, py - r * 0.6, px + r, py + r * 0.6],
                        fill=dust_c + (fade,))
                over.alpha_composite(puff.filter(ImageFilter.GaussianBlur(2.2)))
        comp = Image.new("RGBA", base.size, (0, 0, 0, 0))
        comp.alpha_composite(under)
        comp.alpha_composite(base)
        comp.alpha_composite(over)
        out.append(comp)
    return out


def draw_wire(images, active=None, width: float = 1.6, sway: float = 2.4,
              glint: float = 0.55, body_rgb=None, glint_rgb=None, axes=None):
    """A flyline from the character's harness point, straight up out of frame.

    The axis' BASE is the harness -- the waist -- and the line goes to the top
    edge, not along the body: a wire is vertical whatever the person on it is
    doing, and that is exactly what tells the audience she is not jumping.
    """
    live = None if active is None else set(active)
    body = tuple(body_rgb) if body_rgb else WIRE_BODY
    hot = tuple(glint_rgb) if glint_rgb else WIRE_GLINT
    axes = axes if axes is not None else [blade_axis(im) for im in images]
    out = []
    for i, base in enumerate(images):
        if axes[i] is None or (live is not None and i not in live):
            out.append(base.copy())
            continue
        ax, ay = axes[i][0]
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw = blending_draw(layer)
        # A taut wire still moves; the sway is what stops it reading as a scratch
        # on the film.
        steps = 10
        points = []
        for k in range(steps + 1):
            f = k / steps
            y = ay * (1.0 - f)
            points.append((ax + math.sin(f * math.pi * 1.5 + i * 0.9) * sway * f, y))
        draw.line(points, fill=body + (214,), width=max(1, int(round(width))))
        if glint > 0.0:
            draw.line(points[: steps // 2], fill=hot + (int(210 * glint),), width=1)
        comp = Image.new("RGBA", base.size, (0, 0, 0, 0))
        comp.alpha_composite(base)
        comp.alpha_composite(layer)
        out.append(comp)
    return out


MEND_RING = (168, 236, 250)
MEND_CORE = (250, 255, 255)


def draw_mend(images, active=None, rings: int = 3, rise: float = 26.0,
              radius: float = 15.0, period: int = 4, alpha: int = 150,
              core_alpha: int = 120, blur: float = 1.8, body_rgb=None,
              core_rgb=None, axes=None):
    """Soft rings rising off a body point: something being PUT BACK.

    ⭐ IT RISES AND IT DOES NOT REACH. Every other effect here travels outward
    from the character because it is going to hurt somebody; this one has to read
    as the opposite, so the rings go UP, stay inside her own silhouette's width,
    and fade at the top rather than opening into a cone.

    The axis' BASE is where the hand is working -- the wound, not the weapon.
    """
    live = None if active is None else set(active)
    body = tuple(body_rgb) if body_rgb else MEND_RING
    core = tuple(core_rgb) if core_rgb else MEND_CORE
    axes = axes if axes is not None else [blade_axis(im) for im in images]
    out = []
    for i, base in enumerate(images):
        if axes[i] is None or (live is not None and i not in live):
            out.append(base.copy())
            continue
        cx, cy = axes[i][0]
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw = blending_draw(layer)
        for k in range(rings):
            phase = ((i + k * period / rings) % period) / period
            y = cy - rise * phase
            r = radius * (0.45 + 0.55 * phase)
            a = int(alpha * (1.0 - phase) ** 1.4)
            if a <= 3:
                continue
            draw.ellipse([cx - r, y - r * 0.34, cx + r, y + r * 0.34],
                         outline=body + (a,), width=2)
        glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
        blending_draw(glow).ellipse(
            [cx - radius * 0.7, cy - radius * 0.5, cx + radius * 0.7, cy + radius * 0.5],
            fill=core + (core_alpha,))
        layer.alpha_composite(glow.filter(ImageFilter.GaussianBlur(radius * 0.4)))
        comp = Image.new("RGBA", base.size, (0, 0, 0, 0))
        comp.alpha_composite(base)
        comp.alpha_composite(layer.filter(ImageFilter.GaussianBlur(blur)))
        out.append(comp)
    return out


#: Which drawing function each authored effect uses. A spec names one of these,
#: and the hit volume below is built from the SAME name, so an effect cannot be
#: added that draws light in a shape nothing hits in.
EFFECT_DRAW = {
    "trail": lambda: draw_trail,
    "poke": lambda: draw_poke,
    "wind": lambda: draw_wind,
    "reentry": lambda: draw_reentry,
    "muzzle": lambda: draw_muzzle,
    "beam": lambda: draw_beam,
    # Stage machinery. Neither publishes a hit volume: a trap door does not hurt
    # anyone and neither does a wire, so their specs carry no `hitbox.active` and
    # name their live frames on their own style block instead.
    "trapdoor": lambda: draw_trapdoor,
    "wire": lambda: draw_wire,
    "mend": lambda: draw_mend,
}


def volume_polygon(axes, i, effect: str, first: int, swept: dict, poke: dict,
                   reentry: dict | None = None):
    """The hit volume for frame `i`, in the shape of whatever effect it draws.

    One function so the promise and the hit stay the same object: a swept effect
    hits along its ribbon, a thrust hits along its lance, and a re-entry plume
    hits inside its cone. Nothing gets to hit in a shape the player was never
    shown -- which is the point of a smash drawing a big cone in the first
    place.

    A `wind` whoosh sweeps like a ribbon does, so it shares the swept hull: the
    streaks are a way of DRAWING that travel, not a different claim about it.
    """
    if effect == "poke":
        return poke_polygon(axes, i, poke.get("extend", 1.30), poke.get("width", 13.0),
                            poke.get("waist", 0.66), poke.get("inner", 0.10))
    if effect == "muzzle":
        shot = reentry or {}
        polys = [
            muzzle_polygon(axes, i, shot.get("reach", 1.5), shot.get("flare", 0.55), offset)
            for offset in (shot.get("spread") or [0.0])
        ]
        points = [p for poly in polys if poly for p in poly]
        return _hull(points) if len(points) >= 3 else None
    if effect == "beam":
        shot = reentry or {}
        return beam_polygon(axes, i, shot.get("reach", 8.0), shot.get("width", 0.30))
    if effect == "reentry":
        cone = reentry or {}
        return reentry_polygon(axes, i, cone.get("spread", 1.15),
                               cone.get("extend", 1.12), cone.get("trail", 1.05))
    return hit_polygon(axes, i, swept.get("reach", 1.0), swept.get("linger"),
                       first, swept.get("extend", 1.0), swept.get("inflate", 0.0))


def draw_hitboxes(images, reach: float = 1.0, linger: int | None = None, windows=None,
                  extend: float = 1.0, inflate: float = 0.0, effect: str = "trail",
                  poke=None, axes=None, reentry=None):
    """`active` limits the overlay to the frames that actually connect.

    A swing is only dangerous for part of its travel; drawing a volume on the
    wind-up and the recovery makes an attack look far more threatening than it
    is, which is the opposite of what a review image is for.
    """
    # Measured on the RAW frames when the caller supplies them, and it must be:
    # every effect draws light brighter than BLADE_LUM, so re-measuring here
    # reads the flash as part of the sword and drags a hitbox vertex with it.
    axes = axes if axes is not None else [blade_axis(im) for im in images]
    windows = windows or []
    out = []
    for i, base in enumerate(images):
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        first = window_start(windows, i)
        poly = (None if first is None
                else volume_polygon(axes, i, effect, first,
                                    dict(reach=reach, linger=linger, extend=extend,
                                         inflate=inflate), poke or {}, reentry or {}))
        if poly is not None and len(poly) >= 3:
            draw = blending_draw(layer)
            # Light enough that the ribbon's own colour still reads through it --
            # the overlay is a measurement, and it should not repaint the thing
            # being measured. The outline carries the shape.
            draw.polygon(poly, fill=HITBOX + (26,))
            draw.line(list(poly) + [poly[0]], fill=HITBOX + (210,), width=1)
        comp = base.copy()
        comp.alpha_composite(layer)
        out.append(comp)
    return out


def composite_authored_effect(images, spec: dict, axes=None):
    """Composite one clip's authored effect onto its rendered frames.

    THE PUBLISH PATH. `spec` is the same `*.spec.json` the reviewer reads, so
    what ships is what was reviewed — there is no second set of numbers.

    Review overlays (the hit volumes, the floor rule) are deliberately NOT
    applied: they answer questions about the art, they are not the art.

    `axes` lets a caller state where the blade is instead of leaving
    `blade_axis` to infer it from brightness. That inference only holds for a
    figure darker than its steel; on a character with skin and pale shoes it
    reads the face as the blade. A rig that gives the weapon its own part
    already knows the answer and should say so.
    """
    effect = spec.get("effect", "trail")
    style = dict(spec.get(effect) or {})
    if axes is None:
        axes = [blade_axis(image) for image in images]
    windows = hit_windows(spec.get("hitbox") or {})
    if windows:
        # One window for both: a frame that cannot hurt anyone does not sweep
        # light, which is what keeps a charge-up dark.
        style.setdefault("active", [f for window in windows for f in window])
    if effect not in EFFECT_DRAW:
        raise ValueError(f"unknown authored effect {effect!r}; have {sorted(EFFECT_DRAW)}")
    return EFFECT_DRAW[effect]()(images, axes=axes, **style)


def hit_shape(spec: dict) -> dict:
    """Hit-volume geometry, DERIVED from the ribbon rather than declared beside it.

    The hitbox is the trail: its inner edge is the ribbon's inner edge, its
    window is how long the ribbon lingers, and it never reaches past the blade.
    Growing a hitbox therefore means making the swing sweep LONGER, which a
    player can see — not quietly inflating a box beyond the art, which they
    cannot. One source, so the two cannot drift.
    """
    # The effect's OWN style block, not `trail` by name: a whoosh derives its
    # volume from the whoosh it drew, or a brawler's hitbox would silently come
    # from a ribbon the character never draws.
    style = spec.get(spec.get("effect", "trail")) or {}
    hitbox = spec.get("hitbox") or {}
    return {
        "reach": round(1.0 - style.get("inner", 0.58), 4),
        "linger": style.get("window", 3) + 1,
        "extend": hitbox.get("extend", 1.0),
        "inflate": hitbox.get("inflate", 0.0),
    }


def authored_hit_volume(images, spec: dict, axes=None):
    """The whole swing's hit volume, as one convex polygon in frame pixels.

    THE PUBLISH PATH for the volume, next to the one for the ribbon. The runtime
    seam (`manifest_attack_hitbox_world`) prefers an authored `poly` over a
    coarse bbox precisely so a blade arc can hit in the shape it was drawn in —
    it had simply never been given one, so every swing fell back to a rectangle
    the reviewer had never seen.

    One polygon per animation, not per frame: that is what the seam reads, so
    this is the hull of every ACTIVE frame's volume — the ground the swing
    covers while it can hurt, which is the same claim the lingering ribbon
    makes.
    """
    windows = hit_windows(spec.get("hitbox") or {})
    if not windows:
        return None
    effect = spec.get("effect", "trail")
    swept = hit_shape(spec)
    poke = spec.get("poke") or {}
    reentry = spec.get("reentry") or spec.get("muzzle") or spec.get("beam") or {}
    if axes is None:
        axes = [blade_axis(image) for image in images]
    points: list[tuple[float, float]] = []
    for window in windows:
        for i in window:
            if i >= len(axes):
                continue
            polygon = volume_polygon(axes, i, effect, window[0], swept, poke, reentry)
            if polygon:
                points.extend(polygon)
    if len(points) < 3:
        return None
    return [(float(x), float(y)) for x, y in _hull(points)]
