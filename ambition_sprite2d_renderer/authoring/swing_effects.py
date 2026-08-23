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


def volume_polygon(axes, i, effect: str, first: int, swept: dict, poke: dict):
    """The hit volume for frame `i`, in the shape of whatever effect it draws.

    One function so the promise and the hit stay the same object: a swept effect
    hits along its ribbon, a thrust hits along its lance. Nothing gets to hit in
    a shape the player was never shown.
    """
    if effect == "poke":
        return poke_polygon(axes, i, poke.get("extend", 1.30), poke.get("width", 13.0),
                            poke.get("waist", 0.66), poke.get("inner", 0.10))
    return hit_polygon(axes, i, swept.get("reach", 1.0), swept.get("linger"),
                       first, swept.get("extend", 1.0), swept.get("inflate", 0.0))


def draw_hitboxes(images, reach: float = 1.0, linger: int | None = None, windows=None,
                  extend: float = 1.0, inflate: float = 0.0, effect: str = "trail",
                  poke=None, axes=None):
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
                                         inflate=inflate), poke or {}))
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


def composite_authored_effect(images, spec: dict):
    """Composite one clip's authored effect onto its rendered frames.

    THE PUBLISH PATH. `spec` is the same `*.spec.json` the reviewer reads, so
    what ships is what was reviewed — there is no second set of numbers.

    Review overlays (the hit volumes, the floor rule) are deliberately NOT
    applied: they answer questions about the art, they are not the art.
    """
    effect = spec.get("effect", "trail")
    style = dict(spec.get(effect) or {})
    axes = [blade_axis(image) for image in images]
    windows = hit_windows(spec.get("hitbox") or {})
    if windows:
        # One window for both: a frame that cannot hurt anyone does not sweep
        # light, which is what keeps a charge-up dark.
        style.setdefault("active", [f for window in windows for f in window])
    draw = draw_poke if effect == "poke" else draw_trail
    return draw(images, axes=axes, **style)
