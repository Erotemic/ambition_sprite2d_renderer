"""Author the Bad Apple family as labeled SVG parts.

The apple body, notch, leaf, and stem reuse the shape controls of GNU-ton's
projectile. This file chooses the enemy faces, expression poses, and effects.
All values are character art; this file does not define game behavior.
"""

from __future__ import annotations

from functools import lru_cache
from io import BytesIO
import math
from pathlib import Path
from typing import Mapping

from PIL import Image

from ...authoring.sheet_build import build_sheet
from ...authoring.svg_parts import _svg_to_png_bytes
from ..props._apple_geometry import LEAF_FAR, LEAF_MAIN, STEM_MAIN
from ..props.gnu_ton_apple import _make_body_mask

FRAME_SIZE = (256, 256)
SHEET_KEYS = ("canonical", "canonical_transparent", "spritesheet", "yaml", "ron", "actor", "preview")

# The collision and gravity rules are not authored here. These are visual poses.
BAD_ROWS = (
    ("idle", 6, 140),
    ("walk", 8, 85),
    ("chomp", 7, 75),
    ("hurt", 3, 110),
    ("death", 7, 100),
    ("notice", 4, 110),
    ("windup", 4, 90),
    ("attack_side", 7, 75),
)
GRAVITY_ROWS = (
    ("idle", 8, 115),
    ("float", 8, 100),
    ("charge", 7, 95),
    ("flip", 8, 85),
    ("hurt", 3, 100),
    ("death", 7, 95),
    ("notice", 4, 110),
    ("windup", 4, 90),
    ("attack_side", 7, 95),
)

# The rows an enemy reads by (`docs/planning/game/enemy-patterns.md`), drawn
# from the apple's own attack: `notice`, a hop and a glare as it first sees
# you; `windup`, the attack's widest frame held, leaning back (every frame the
# full pose, with a shiver); `attack_side`, the attack played through. Each
# entry: the source row, its frame count, the source frame of each of ours
# (None plays it through), and the hop/lean of the pose.
DERIVED_ROWS = {
    "bad_apple": {
        "notice": ("chomp", 7, (0, 1, 1, 1), "hop"),
        "windup": ("chomp", 7, (3, 3, 3, 3), "lean"),
        "attack_side": ("chomp", 7, None, None),
    },
    # The Gravity Apple's are drawn by its own art (`_gravity_apple_art.DERIVED`).
    "gravity_apple": {},
}


def _n(v: float) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".")


def _points(points: tuple[tuple[int, int], ...]) -> str:
    return " ".join(f"{x},{y}" for x, y in points)


@lru_cache(maxsize=1)
def _body_path() -> str:
    """Trace the projectile's authoritative body mask into one SVG silhouette."""
    mask = _make_body_mask()
    top: list[tuple[int, int]] = []
    bottom: list[tuple[int, int]] = []
    for x in range(0, mask.width, 2):
        ys = [y for y in range(mask.height) if mask.getpixel((x, y)) >= 128]
        if ys:
            top.append((x, ys[0]))
            bottom.append((x, ys[-1]))
    points = top + list(reversed(bottom))
    if not points:
        raise ValueError("The shared apple silhouette is empty")
    return "M" + " L".join(f"{x} {y}" for x, y in points) + " Z"


def _definitions(gravity: bool) -> str:
    if gravity:
        top, mid, bottom, light, shadow = "#f25b66", "#ca254b", "#641e59", "#fff0a0", "#252044"
        leaf_light, leaf_dark = "#b6e86e", "#427e61"
    else:
        top, mid, bottom, light, shadow = "#ec5a43", "#aa2437", "#611c2b", "#ffd995", "#321a21"
        leaf_light, leaf_dark = "#899b4b", "#475435"
    return f"""
    <defs>
      <linearGradient id="apple-skin" x1="0.16" y1="0.05" x2="0.9" y2="0.98">
        <stop offset="0" stop-color="{top}"/><stop offset="0.42" stop-color="{mid}"/>
        <stop offset="1" stop-color="{bottom}"/>
      </linearGradient>
      <radialGradient id="apple-light" cx="30%" cy="25%" r="68%">
        <stop offset="0" stop-color="{light}" stop-opacity=".68"/>
        <stop offset=".55" stop-color="{light}" stop-opacity=".08"/>
        <stop offset="1" stop-color="{light}" stop-opacity="0"/>
      </radialGradient>
      <radialGradient id="bruise" cx="50%" cy="50%" r="62%">
        <stop offset="0" stop-color="{shadow}" stop-opacity=".95"/>
        <stop offset="1" stop-color="{shadow}" stop-opacity="0"/>
      </radialGradient>
      <linearGradient id="apple-leaf" x1=".2" y1="0" x2=".9" y2="1">
        <stop offset="0" stop-color="{leaf_light}"/>
        <stop offset="1" stop-color="{leaf_dark}"/>
      </linearGradient>
      <clipPath id="apple-clip" clipPathUnits="userSpaceOnUse">
        <path d="{_body_path()}"/>
      </clipPath>
    </defs>"""


def _g(part: str, bone: str, z: int, content: str, transform: str = "") -> str:
    attr = f' transform="{transform}"' if transform else ""
    return (
        f'<g id="{part}" data-rig-part="{part}" data-rig-bone="{bone}" '
        f'data-rig-z="{z}"{attr}><title>{part.replace("_", " ")}</title>{content}</g>'
    )


def _pulse(progress: float, center: float, width: float) -> float:
    """Smooth, triangular-in-time expression envelope with eased endpoints."""
    x = max(0.0, 1.0 - abs(progress - center) / width)
    return x * x * (3.0 - 2.0 * x)


def _bad_eyes(glance: float, blink_scale: float, bite: float) -> str:
    """A predatory squint with dark sockets, sickly eyes, and slit pupils.

    Opposing brow angles, rather than giant round whites, establish menace.
    The face itself stays upright for later engine-controlled whole-body roll.
    """
    l_x = 186 + 0.35 * glance
    r_x = 319 + 0.25 * glance
    sockets = (
        '<path d="M137 268 Q159 229 218 250 Q237 270 214 307 '
        'Q170 313 143 286Z" fill="#42121c" stroke="#341018" stroke-width="7"/>'
        '<path d="M273 262 Q314 222 362 252 Q372 283 345 299 '
        'Q302 311 284 289Z" fill="#42121c" stroke="#341018" stroke-width="7"/>'
    )
    squint = 7 * bite
    eyeballs = (
        f'<path d="M153 {_n(275+squint)} Q180 {_n(252+squint)} 216 {_n(271+squint)} '
        f'Q198 {_n(294-squint)} 160 {_n(288-squint)}Z" '
        'fill="#dbe399" stroke="#25111a" stroke-width="5"/>'
        f'<path d="M283 {_n(270+squint)} Q323 {_n(242+squint)} 352 {_n(263+squint)} '
        f'Q339 {_n(285-squint)} 293 {_n(288-squint)}Z" '
        'fill="#e9e6a7" stroke="#25111a" stroke-width="5"/>'
        f'<path d="M{_n(l_x)} {_n(267+squint)} '
        f'Q{_n(l_x+7)} {_n(276+squint)} {_n(l_x+1)} {_n(287-squint)} '
        f'Q{_n(l_x-7)} {_n(280-squint)} {_n(l_x)} {_n(267+squint)}Z" fill="#17121a"/>'
        f'<path d="M{_n(r_x)} {_n(258+squint)} '
        f'Q{_n(r_x+7)} {_n(268+squint)} {_n(r_x+1)} {_n(280-squint)} '
        f'Q{_n(r_x-7)} {_n(274-squint)} {_n(r_x)} {_n(258+squint)}Z" fill="#17121a"/>'
        f'<circle cx="{_n(l_x-4)}" cy="{_n(271+squint)}" r="3" fill="#fff2bf" opacity=".9"/>'
        f'<circle cx="{_n(r_x-4)}" cy="{_n(264+squint)}" r="3" fill="#fff2bf" opacity=".9"/>'
    )
    return sockets + (
        '<g transform="translate(0 278) '
        f'scale(1 {_n(blink_scale)}) translate(0 -278)">{eyeballs}</g>'
    )


def _bad_maw(bite: float) -> str:
    """A broad, uneven bite with individually recognizable ivory fangs."""
    open_bite = min(1.0, max(0.0, bite))
    # A closed snarl remains threatening; opening stretches the black void,
    # not the whole fruit. The teeth stay attached to their respective jaws.
    x0 = 160 - 15 * open_bite
    x1 = 360 + 14 * open_bite
    y0 = 351 - 22 * open_bite
    y1 = 423 + 32 * open_bite
    # The upper tooth roots are slightly irregular. Use solid triangles,
    # rather than a continuous zigzag line, to remain visible at 1x scale.
    top_fangs = (
        (x0 + 18, y0 + 7, x0 + 37, y0 + 10, x0 + 31, y0 + 37 + 8 * open_bite),
        (x0 + 50, y0 - 5, x0 + 78, y0 + 1, x0 + 65, y0 + 38 + 14 * open_bite),
        (x0 + 91, y0 + 7, x0 + 127, y0 + 6, x0 + 109, y0 + 54 + 13 * open_bite),
        (x0 + 142, y0 + 0, x0 + 171, y0 - 1, x0 + 159, y0 + 34 + 13 * open_bite),
        (x1 - 26, y0 + 8, x1 - 9, y0 + 15, x1 - 23, y0 + 43 + 9 * open_bite),
    )
    lower_fangs = (
        (x0 + 28, y1 - 21, x0 + 45, y1 - 33 - 14 * open_bite, x0 + 57, y1 - 7),
        (x0 + 74, y1 - 2, x0 + 92, y1 - 44 - 10 * open_bite, x0 + 112, y1 - 7),
        (x0 + 125, y1 - 3, x0 + 144, y1 - 38 - 15 * open_bite, x0 + 163, y1 - 14),
        (x1 - 38, y1 - 12, x1 - 22, y1 - 43 - 13 * open_bite, x1 - 8, y1 - 25),
    )
    jaw = (
        f'<path d="M{_n(x0)} {_n(y0+5)} '
        f'Q{_n(x0+38)} {_n(y0-24)} {_n(x0+93)} {_n(y0-10)} '
        f'Q{_n(x0+145)} {_n(y0-27)} {_n(x1)} {_n(y0+11)} '
        f'Q{_n(x1+10)} {_n(y1-18)} {_n(x1-36)} {_n(y1-3)} '
        f'Q260 {_n(y1+15)} {_n(x0+43)} {_n(y1-7)} '
        f'Q{_n(x0-11)} {_n(y1-25)} {_n(x0)} {_n(y0+5)}Z" '
        'fill="#200810" stroke="#351018" stroke-width="11" stroke-linejoin="round"/>'
        f'<path d="M{_n(x0+6)} {_n(y0+13)} '
        f'Q256 {_n(y0-3)} {_n(x1-6)} {_n(y0+17)}" '
        'fill="none" stroke="#8f3542" stroke-width="7" stroke-linecap="round" opacity=".7"/>'
        f'<path d="M{_n(x0+50)} {_n(y1-14)} Q260 {_n(y1+3)} '
        f'{_n(x1-44)} {_n(y1-17)}" fill="none" stroke="#a64156" '
        'stroke-width="11" stroke-linecap="round" opacity=".6"/>'
    )
    upper = ''.join(
        f'<path d="M{_n(a)} {_n(b)} L{_n(c)} {_n(d)} L{_n(e)} {_n(f)}Z" '
        'fill="#f5e6b9" stroke="#c8a78a" stroke-width="2" stroke-linejoin="round"/>'
        for a,b,c,d,e,f in top_fangs
    )
    lower = ''.join(
        f'<path d="M{_n(a)} {_n(b)} L{_n(c)} {_n(d)} L{_n(e)} {_n(f)}Z" '
        'fill="#ead4a6" stroke="#b58c7a" stroke-width="2" stroke-linejoin="round"/>'
        for a,b,c,d,e,f in lower_fangs
    )
    # The lip creases make the jaw asymmetric, without a detachable shadow.
    wrinkles = (
        f'<path d="M{_n(x0-5)} {_n(y0-12)} l-18 -10 M{_n(x1+7)} {_n(y0+13)} '
        'l20 -13" fill="none" stroke="#4e1922" stroke-width="9" '
        'stroke-linecap="round"/>'
    )
    return jaw + upper + lower + wrinkles


def _face(animation: str, frame: int, count: int, gravity: bool) -> str:
    """Animate facial performance independently of runtime whole-body rotation.

    A gameplay rolling pose must rotate the sprite/actor continuously; the
    authored frames instead supply looks, blink, anticipation, bite and recoil.
    """
    phase = frame / count * math.tau
    progress = frame / max(1, count - 1)
    blink = _pulse(frame / count, .80, .20) if animation == "idle" else 0.0
    bite = _pulse(progress, .53, .52) if animation == "chomp" else 0.0
    charge = _pulse(progress, .60, .57) if animation == "charge" else 0.0
    inverted = _pulse(progress, .55, .55) if animation == "flip" else 0.0
    hurt = animation == "hurt"
    dying = animation == "death"
    death = _pulse(progress, 1.0, .72) if dying else 0.0
    glance = (5 * math.sin(phase)) if animation in ("idle", "float", "walk") else 0.0
    if animation == "walk":
        glance += 8  # Look into the direction of travel, not around the roll.
    elif animation == "flip":
        glance += 11 * math.sin(progress * math.tau)
    elif animation in ("charge", "chomp"):
        glance += 5
    squint = (0.28 * bite if not gravity else 0.12 * (charge + inverted))
    blink_scale = max(.12, 1.0 - .88 * blink - squint)
    pupil_up = (-8 * charge) if gravity else (3 * bite)
    if animation == "flip":
        pupil_up += -18 * math.sin(progress * math.tau)

    if hurt:
        face_eyes = (
            '<path d="M166 283 l52 -13 m84 2 l42 17" fill="none" stroke="#27131d" '
            'stroke-width="14" stroke-linecap="round"/>'
        )
    else:
        # Blend eye highlights continuously during charging; no color pop.
        tint = charge if gravity else 0.0
        eye_color = "#{:02x}{:02x}{:02x}".format(
            round(255 - 56 * tint), round(249 + 4 * tint), round(230 + 25 * tint)
        )
        pupil_x_left = 195 + glance
        pupil_x_right = 323 + glance * .8
        pupil_y = 285 + pupil_up
        face_eyes = (
            f'<path d="M155 271 Q169 239 205 242 Q227 255 220 300 Q189 323 163 296Z" '
            f'fill="{eye_color}" stroke="#351c25" stroke-width="9"/>'
            f'<path d="M290 249 Q316 229 341 249 Q358 269 347 304 Q316 316 294 295Z" '
            f'fill="{eye_color}" stroke="#351c25" stroke-width="9"/>'
            f'<ellipse cx="{_n(pupil_x_left)}" cy="{_n(pupil_y)}" rx="14" ry="20" fill="#251b29"/>'
            f'<ellipse cx="{_n(pupil_x_right)}" cy="{_n(pupil_y - 5)}" rx="12" ry="17" fill="#251b29"/>'
            f'<circle cx="{_n(pupil_x_left - 5)}" cy="{_n(pupil_y - 8)}" r="6" fill="#fffef4"/>'
            f'<circle cx="{_n(pupil_x_right - 4)}" cy="{_n(pupil_y - 12)}" r="5" fill="#fffef4"/>'
        )
        face_eyes = (
            '<g transform="translate(0 278) '
            f'scale(1 {_n(blink_scale)}) translate(0 -278)">{face_eyes}</g>'
        )
        if dying:
            crosses = (
                '<path d="M167 259 l40 43 m0 -43 l-40 43 '
                'M302 257 l40 43 m0 -43 l-40 43" '
                'stroke="#25171f" stroke-width="13" '
                'stroke-linecap="round" fill="none"/>'
            )
            face_eyes = (
                f'<g opacity="{_n(1 - death)}">{face_eyes}</g>'
                f'<g opacity="{_n(death)}">{crosses}</g>'
            )

    if not gravity and not hurt and not dying:
        face_eyes = _bad_eyes(glance, blink_scale, bite)

    brow_lift = (-8 * charge if gravity else 7 * bite) + 3 * math.sin(phase)
    if gravity:
        brows = (
            f'<path d="M148 {_n(237+brow_lift)} Q183 {_n(211+brow_lift)} 218 {_n(228+brow_lift)} '
            f'M290 {_n(226+brow_lift)} Q327 {_n(202+brow_lift)} 356 {_n(229+brow_lift)}" '
            'fill="none" stroke="#4e203b" stroke-width="17" stroke-linecap="round"/>'
        )
    else:
        # Heavy inner-down brows partially cover the eyes rather than floating
        # above large round whites. The crooked heights give him a sneer.
        brows = (
            f'<path d="M133 {_n(226+brow_lift)} Q178 {_n(217+brow_lift)} 226 {_n(254+brow_lift)} '
            f'L214 {_n(269+brow_lift)} Q173 {_n(249+brow_lift)} 143 {_n(252+brow_lift)}Z" '
            'fill="#45151d" stroke="#321018" stroke-width="5" stroke-linejoin="round"/>'
            f'<path d="M277 {_n(255+brow_lift)} Q324 {_n(211+brow_lift)} 373 {_n(228+brow_lift)} '
            f'L357 {_n(256+brow_lift)} Q316 {_n(245+brow_lift)} 285 {_n(272+brow_lift)}Z" '
            'fill="#45151d" stroke="#321018" stroke-width="5" stroke-linejoin="round"/>'
        )

    if hurt:
        mouth = '<ellipse cx="263" cy="372" rx="19" ry="25" fill="#34131d" stroke="#42191d" stroke-width="6"/>'
    elif dying:
        mouth = (
            f'<path d="M217 {_n(375 + 7 * death)} Q256 {_n(359 + 15 * death)} '
            f'299 {_n(375 + 7 * death)}" fill="none" stroke="#31161c" '
            'stroke-width="13" stroke-linecap="round"/>'
        )
    elif gravity:
        # A smooth fade from a crooked grin to the small round mouth of a
        # gravity reversal. The orbit supplies the directional telegraph.
        surprise = max(charge, inverted)
        grin = (
            '<path d="M218 360 Q270 395 327 352 Q318 379 275 391 Q238 389 218 360Z" '
            'fill="#351b3e" stroke="#412038" stroke-width="8"/>'
            '<path d="M247 378 Q277 388 305 369" fill="none" '
            'stroke="#f8b7c8" stroke-width="6"/>'
        )
        mouth = (
            f'<g opacity="{_n(1.0 - surprise)}">{grin}</g>'
            f'<g opacity="{_n(surprise)}">'
            f'<ellipse cx="274" cy="370" rx="{_n(18 + 8 * surprise)}" '
            f'ry="{_n(14 + 19 * surprise)}" fill="#331c40" '
            'stroke="#4e254a" stroke-width="7"/>'
            '<path d="M260 391 Q275 383 289 393" stroke="#f8b7c8" '
            'stroke-width="5" fill="none"/></g>'
        )
    else:
        mouth = _bad_maw(bite)
    # Small cheeks are part of the face/fruit, never detached contact shading.
    cheeks = (
        '<path d="M149 331 q9 6 17 2 M350 326 q9 4 17 -4" '
        'stroke="#ffb69b" stroke-width="7" fill="none" opacity=".26" '
        'stroke-linecap="round"/>'
    ) if gravity else ''
    return _g("eyes", "face", 30, brows + face_eyes) + _g("mouth", "face", 31, mouth + cheeks)

def _body(gravity: bool) -> str:
    black = "#36202a" if gravity else "#3c2224"
    core = (
        f'<path d="{_body_path()}" fill="url(#apple-skin)" stroke="{black}" '
        'stroke-width="10" stroke-linejoin="round"/>'
        '<g clip-path="url(#apple-clip)">'
        '<ellipse cx="151" cy="225" rx="175" ry="225" fill="url(#apple-light)"/>'
        '<ellipse cx="388" cy="419" rx="178" ry="166" fill="url(#bruise)" opacity=".48"/>'
        '<path d="M123 187 Q164 151 211 172" fill="none" stroke="#ffe0b3" '
        'stroke-width="20" stroke-linecap="round" opacity=".23"/>'
        '<path d="M95 315 Q112 375 153 412" fill="none" stroke="#ffb79a" '
        'stroke-width="10" stroke-linecap="round" opacity=".22"/>'
        '</g>'
    )
    if not gravity:
        core += (
            '<g clip-path="url(#apple-clip)">'
            '<ellipse cx="395" cy="332" rx="104" ry="100" fill="url(#bruise)"/>'
            '<ellipse cx="374" cy="324" rx="17" ry="11" fill="#46252b" opacity=".85"/>'
            '<ellipse cx="413" cy="347" rx="11" ry="17" fill="#552c2e" opacity=".7"/>'
            '<path d="M377 357 Q395 338 419 352" fill="none" stroke="#a4664b" '
            'stroke-width="8" stroke-linecap="round" opacity=".5"/>'
            # Broken, dark infected skin around the bite corner. All details
            # are clipped to the apple itself and remain part of its surface.
            '<path d="M408 219 l-19 26 13 8 -21 24 15 10 -17 17" '
            'fill="none" stroke="#461921" stroke-width="11" '
            'stroke-linecap="round" stroke-linejoin="round" opacity=".8"/>'
            '<path d="M408 219 l-19 26 13 8 -21 24" '
            'fill="none" stroke="#ac6b5b" stroke-width="4" opacity=".5"/>'
            '<path d="M119 309 l-13 19 17 7 -14 16" '
            'fill="none" stroke="#5f2227" stroke-width="9" opacity=".75"/>'
            '</g>'
        )
    else:
        core += (
            '<g clip-path="url(#apple-clip)" opacity=".8">'
            '<path d="M86 343 Q118 408 190 433" fill="none" stroke="#73fff1" '
            'stroke-width="17" stroke-linecap="round"/>'
            '<path d="M118 387 L154 414 L127 428" fill="none" stroke="#d7fff5" '
            'stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>'
            '</g>'
        )
    return _g("apple_body", "fruit", 10, core)


def _leaf_and_stem(gravity: bool, animation: str, frame: int, count: int) -> str:
    phase = math.sin(frame / max(1, count) * math.tau)
    sway = (-11 if animation == "hurt" else 8 * phase)
    stem_x0, stem_y0, stem_x1, stem_y1 = STEM_MAIN
    stem = (
        f'<path d="M{stem_x0} {stem_y0} Q{stem_x0-18} 94 {stem_x1} {stem_y1}" '
        'stroke="#4e2d29" stroke-width="23" fill="none" stroke-linecap="round"/>'
        f'<path d="M{stem_x0} {stem_y0} Q{stem_x0-18} 94 {stem_x1} {stem_y1}" '
        'stroke="#ad7845" stroke-width="12" fill="none" stroke-linecap="round"/>'
    )
    if gravity:
        # Gravity Apple keeps the recognizable bright projectile leaf.
        leaf = (
            f'<polygon points="{_points(LEAF_MAIN)}" fill="url(#apple-leaf)" '
            'stroke="#2f4b38" stroke-width="12" stroke-linejoin="round"/>'
            f'<polygon points="{_points(LEAF_FAR)}" fill="#4b8744" '
            'stroke="#2d5237" stroke-width="9" stroke-linejoin="round"/>'
            '<path d="M268 160 Q346 152 379 134" fill="none" stroke="#d8f19b" '
            'stroke-width="9" stroke-linecap="round"/>'
            '<path d="M330 119 l23 -26 -4 36" fill="#c5ffff" opacity=".8"/>'
        )
    else:
        # A wilted, nibbled leaf, not the big green cap of the projectile.
        # This is attached fruit anatomy; there are no ground shadows.
        leaf = (
            '<path d="M249 151 Q293 115 370 116 L359 133 376 145 '
            'Q351 177 314 177 Q276 176 248 164Z" '
            'fill="url(#apple-leaf)" stroke="#30432e" stroke-width="10" '
            'stroke-linejoin="round"/>'
            '<path d="M255 151 Q216 133 187 166 L214 167 226 186 '
            'Q250 182 267 163Z" fill="#526139" stroke="#30432e" '
            'stroke-width="9" stroke-linejoin="round"/>'
            '<path d="M270 161 Q320 153 355 131" fill="none" '
            'stroke="#b9bd73" stroke-width="6" stroke-linecap="round"/>'
            '<path d="M334 165 l13 -17 12 1" fill="none" '
            'stroke="#35462c" stroke-width="7" stroke-linecap="round"/>'
        )
    return _g("stem", "stem", 40, stem) + _g("leaf", "leaf", 41, leaf, f"rotate({_n(sway)} 270 142)")


def _gravity_fx(animation: str, frame: int, count: int) -> tuple[str, str]:
    phase = frame / max(1, count)
    angle = phase * 360 * (1 if animation != "flip" else -1)
    opacity = ".95" if animation in ("charge", "flip") else ".64"
    scale = 1.10 if animation == "charge" else 1.0
    back = (
        f'<g transform="translate(256 258) rotate({_n(angle)}) scale({_n(scale)}) translate(-256 -258)" '
        f'opacity="{opacity}">'
        '<ellipse cx="256" cy="258" rx="194" ry="155" fill="none" '
        'stroke="#72eeff" stroke-width="11" stroke-dasharray="185 70 28 85"/>'
        '<path d="M83 201 l-19 -25 29 -10" fill="none" stroke="#bafaff" '
        'stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>'
        '<path d="M425 310 l24 28 -32 7" fill="none" stroke="#bafaff" '
        'stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>'
        '</g>'
        '<circle cx="90" cy="355" r="10" fill="#b6faff" opacity=".95"/>'
        '<circle cx="439" cy="157" r="7" fill="#d2ffff" opacity=".9"/>'
    )
    front = (
        '<g opacity=".9">'
        '<path d="M418 226 Q452 244 437 284" stroke="#91fbfa" '
        'stroke-width="10" stroke-linecap="round" fill="none"/>'
        '<path d="M428 268 l11 19 16 -16" stroke="#e5fffd" '
        'stroke-width="9" stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
        '</g>'
    )
    return _g("gravity_orbit_back", "gravity", 0, back), _g("gravity_orbit_front", "gravity", 50, front)


def frame_svg(kind: str, animation: str, frame: int, count: int) -> str:
    """Return an editable, part-labeled, *unrotated* expression sprite.

    Walk is a rolling-expression loop, not discrete rotational keyframes.
    Flip conveys a gravity reversal through face, deformation and orbit only.
    The engine will need to drive continuous sprite rotation separately.
    """
    if kind not in {"bad_apple", "gravity_apple"}:
        raise ValueError(f"Unknown apple family member: {kind}")
    rows = dict((name, frames) for name, frames, _ in (GRAVITY_ROWS if kind == "gravity_apple" else BAD_ROWS))
    if animation not in rows:
        raise ValueError(f"Unknown {kind} animation: {animation}")
    if count < 1 or not 0 <= frame < count:
        raise ValueError("The frame index must be within the animation.")
    derived = DERIVED_ROWS[kind].get(animation)
    if derived is not None:
        source, source_count, frames, pose = derived
        if frames is None:
            return _frame_svg(kind, source, round(frame * (source_count - 1) / max(1, count - 1)), source_count)
        progress = frame / max(1, count - 1)
        if pose == "hop":
            nudge = (0.0, -14 * math.sin(math.pi * min(1.0, progress * 1.6)), .96, 1.05)
        else:
            nudge = (-7.0 + (1.2 if frame % 2 else -1.2), 2.0, .93, 1.07)
        return _frame_svg(kind, source, frames[frame], source_count, nudge)
    return _frame_svg(kind, animation, frame, count)


def _frame_svg(kind: str, animation: str, frame: int, count: int, nudge=(0.0, 0.0, 1.0, 1.0)) -> str:
    """`frame_svg` of one of the authored rows, moved by `nudge` (dx, dy, sx, sy)."""
    gravity = kind == "gravity_apple"
    phase = frame / count * math.tau
    progress = frame / max(1, count - 1)
    bite = _pulse(progress, .53, .52) if animation == "chomp" else 0.0
    charge = _pulse(progress, .60, .57) if animation == "charge" else 0.0
    flip = _pulse(progress, .55, .55) if animation == "flip" else 0.0

    # Small translation/deformation does not substitute for the engine's
    # physical rolling animation, which should be smooth and speed-dependent.
    x = 0.0
    y = 3 * math.sin(phase)
    sx = 1.0
    sy = 1.0
    if gravity:
        y += -18 + 7 * math.sin(phase)
        sx += .022 * math.sin(phase) + .040 * charge - .035 * flip
        sy -= .022 * math.sin(phase) + .030 * charge - .055 * flip
    elif animation == "walk":
        x += 3 * math.sin(phase)
        sx += .028 * math.sin(phase)
        sy -= .025 * math.sin(phase)
    elif animation == "chomp":
        x += 6 * bite
        sx += .08 * bite
        sy -= .055 * bite
    elif animation == "idle":
        sx += .018 * math.sin(phase)
        sy -= .018 * math.sin(phase)
    if animation == "hurt":
        x += (-7 if frame % 2 == 0 else 8)
        sx *= .96
        sy *= 1.03
    elif animation == "death":
        progress_eased = progress * progress * (3 - 2 * progress)
        sx *= 1.0 + .14 * progress_eased
        sy *= 1.0 - .33 * progress_eased
        y += 12 * progress_eased

    fruit = _body(gravity) + _face(animation, frame, count, gravity) + _leaf_and_stem(gravity, animation, frame, count)
    pieces: list[str] = []
    if gravity:
        orbit_back, orbit_front = _gravity_fx(animation, frame, count)
        pieces.append(orbit_back)
    pieces.append(_g("fruit_assembly", "fruit", 10, fruit, "translate(82 36) scale(.68)"))
    if gravity:
        pieces.append(orbit_front)

    x += nudge[0]
    y += nudge[1]
    sx *= nudge[2]
    sy *= nudge[3]
    root = _g(
        "character_pose", "root", 0, "".join(pieces),
        f"translate({_n(256 + x)} {_n(254 + y)}) "
        f"scale({_n(sx)} {_n(sy)}) translate(-256 -254)",
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" '
        'viewBox="0 0 512 512" role="img" '
        f'aria-label="{kind.replace("_", " ")} {animation}">'
        + _definitions(gravity) + root + '</svg>'
    )


@lru_cache(maxsize=192)
def frame_png(kind: str, animation: str, frame: int, count: int) -> Image.Image:
    source = frame_svg(kind, animation, frame, count)
    data = _svg_to_png_bytes(source, dpi=96)
    with Image.open(BytesIO(data)) as png:
        return png.convert("RGBA")


def render_family(
    out_dir: str | Path,
    *,
    kind: str,
    rows: tuple[tuple[str, int, int], ...],
    actor_metadata: Mapping[str, object],
) -> list[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result = build_sheet(
        target=kind,
        rows=list(rows),
        render_fn=lambda name, i, n: frame_png(kind, name, i, n),
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        auto_crop=True,
        crop_margin=6,
        actor_metadata=actor_metadata,
        pose_bodies="authored",
    )
    svg_file = out_dir / f"{kind}_idle.svg"
    svg_file.write_text(frame_svg(kind, "idle", 0, rows[0][1]), encoding="utf8")
    return [Path(result[k]) for k in SHEET_KEYS if result.get(k)] + [svg_file]
