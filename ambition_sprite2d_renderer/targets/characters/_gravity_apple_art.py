"""Programmatic, part-authored Gravity Apple artwork.

The normal green apple is dangerous because of the *face* and the uncanny
gravity apparatus, not because its flesh is purple or rotten. The fruit stays
upright in every sprite; whole-body tumbling belongs to the game pose.

Every drawable unit is a self-contained SVG group with a stable part name.
The composite frames are for the conventional sprite-sheet pipeline; render
parts separately to let a future runtime animate rings, fins and satellites
without redrawing or baking their movement into the fruit's pixels.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

SVG_START = '<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 512 512" role="img">'


def _n(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _pulse(x: float, peak: float = .55, width: float = .55) -> float:
    t = min(1.0, max(0.0, 1 - abs(x - peak) / width))
    return t * t * (3 - 2 * t)


@dataclass(frozen=True)
class Part:
    name: str
    parent: str
    z: int
    pivot: tuple[int, int]
    drawing: str  # content in the shared 512x512 viewbox

    def svg_group(self) -> str:
        x, y = self.pivot
        return (
            f'<g id="{self.name}" data-rig-part="{self.name}" '
            f'data-rig-bone="{self.parent}" data-rig-z="{self.z}" '
            f'data-rig-pivot-x="{x}" data-rig-pivot-y="{y}">'
            f'<title>{self.name.replace("_", " ")}</title>{self.drawing}</g>'
        )


def _defs(body_path: str) -> str:
    return f'''
<defs>
  <linearGradient id="green-apple" x1=".16" y1=".06" x2=".89" y2=".98">
    <stop offset="0" stop-color="#d4f27d"/>
    <stop offset=".46" stop-color="#89c442"/>
    <stop offset="1" stop-color="#376f29"/>
  </linearGradient>
  <radialGradient id="apple-sun" cx=".24" cy=".2" r=".76">
    <stop offset="0" stop-color="#f5ffc0" stop-opacity=".72"/>
    <stop offset=".58" stop-color="#edffb6" stop-opacity=".08"/>
    <stop offset="1" stop-color="#ecffb9" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="leaf-green" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#9fdc5d"/>
    <stop offset=".55" stop-color="#548f39"/>
    <stop offset="1" stop-color="#285833"/>
  </linearGradient>
  <clipPath id="apple-cut" clipPathUnits="userSpaceOnUse">
    <path d="{body_path}"/>
  </clipPath>
</defs>'''


def _attached(markup: str, *, local_transform: str = "") -> str:
    # Preserve a common fruit-local coordinate frame for every extracted part.
    child = f'<g transform="{local_transform}">{markup}</g>' if local_transform else markup
    return f'<g transform="translate(82 36) scale(.68)">{child}</g>'


def _satellite(cx: float, cy: float, size: int, *, pale: bool = False) -> str:
    # The diamonds are small rigid bodies, not temporal motion trails.
    main = "#b5faff" if pale else "#85efff"
    return (
        f'<path d="M{_n(cx)} {_n(cy-size)} L{_n(cx+size*.85)} {_n(cy-size*.25)} '
        f'L{_n(cx+size*.74)} {_n(cy+size*.75)} L{_n(cx-size*.46)} {_n(cy+size)} '
        f'L{_n(cx-size)} {_n(cy-size*.22)}Z" '
        f'fill="#24445b" stroke="#203344" stroke-width="5" stroke-linejoin="round"/>'
        f'<path d="M{_n(cx)} {_n(cy-size+3)} L{_n(cx+size*.65)} {_n(cy-size*.15)} '
        f'L{_n(cx+size*.15)} {_n(cy+size*.35)} L{_n(cx-size*.72)} {_n(cy-size*.16)}Z" '
        f'fill="{main}" opacity=".95"/>'
        f'<path d="M{_n(cx+size*.18)} {_n(cy+size*.3)} L{_n(cx+size*.67)} {_n(cy-size*.13)} '
        f'L{_n(cx+size*.65)} {_n(cy+size*.54)} L{_n(cx-size*.38)} {_n(cy+size*.71)}Z" '
        'fill="#3e7598"/>'
    )


def _orbit_parts(progress: float, state: str, charge: float) -> list[Part]:
    # Each arc is a separate, persistent field assembly. Only these parts
    # rotate in the authored preview; a game can replace their pose entirely.
    rotation = 19 * math.sin(progress * math.tau)
    if state == "float":
        rotation += progress * 32
    elif state == "flip":
        rotation -= 74 * _pulse(progress, .55, .62)
    elif state == "charge":
        rotation += 14 * charge
    size = 1 + .075 * charge
    back = (
        '<path d="M72 224 Q132 90 268 93 Q382 86 438 185" '
        'stroke="#7de8ed" stroke-width="10" fill="none" stroke-linecap="round"/>'
        '<path d="M99 365 Q192 429 306 415 Q390 401 426 332" '
        'stroke="#a5d8f2" stroke-width="8" fill="none" stroke-linecap="round"/>'
        '<path d="M105 189 L86 207 L113 218 M417 351 L434 330 L410 315" '
        'stroke="#c5fcf6" stroke-width="9" fill="none" stroke-linecap="round" '
        'stroke-linejoin="round"/>'
    )
    front = (
        '<path d="M55 269 Q145 348 259 346 Q378 344 460 261" '
        'stroke="#88f8f0" stroke-width="12" fill="none" stroke-linecap="round"/>'
        '<path d="M80 320 Q204 386 320 365 Q402 351 448 303" '
        'stroke="#9cbcf1" stroke-width="5" fill="none" stroke-linecap="round" opacity=".75"/>'
        '<path d="M428 283 l28 -23 -33 -9" fill="none" stroke="#e1ffef" '
        'stroke-width="9" stroke-linejoin="round" stroke-linecap="round"/>'
    )
    back_transform = (
        f'translate(256 258) rotate({_n(rotation)}) scale({_n(size)}) translate(-256 -258)'
    )
    front_transform = (
        f'translate(256 258) rotate({_n(-rotation * .6)}) scale({_n(size)}) translate(-256 -258)'
    )
    parts = [
        Part("orbit_back", "gravity", 0, (256, 258), f'<g transform="{back_transform}">{back}</g>'),
        Part("orbit_front", "gravity", 65, (256, 258), f'<g transform="{front_transform}">{front}</g>'),
    ]
    # Nodes can be individually articulated or independently removed.
    satellites = (
        ("satellite_left", 2, 65, 195, 17, 8),
        ("satellite_right", 64, 440, 177, 17, 8),
        ("satellite_upper", 3, 180, 108, 11, 8),
        ("satellite_lower", 66, 365, 412, 12, 8),
    )
    for name, z, cx, cy, radius, _ in satellites:
        theta = (progress * math.tau) * (1 if z < 30 else -1)
        dx = 8 * math.sin(theta) if state in ("float", "charge", "flip") else 0
        dy = 5 * math.cos(theta) if state in ("float", "charge", "flip") else 0
        drawing = (
            f'<g transform="translate({_n(dx)} {_n(dy)})">'
            f'{_satellite(cx, cy, radius, pale=z > 30)}</g>'
        )
        parts.append(Part(name, "gravity", z, (cx, cy), drawing))
    return parts


def _eyes(progress: float, animation: str, charge: float, flip: float) -> tuple[str, str, str]:
    # Opposed lid slopes and narrow pupils establish threat without Bad Apple's
    # giant, toothy mouth. The eyeline is low and nearly horizontal.
    hunt = 4 * math.sin(progress * math.tau)
    if animation in ("charge", "flip"):
        hunt += 9 * max(charge, flip)
    if animation == "hurt":
        hunt = -5
    blink = _pulse(progress, .82, .18) if animation == "idle" else 0.0
    if animation in ("hurt", "death"):
        blink = 1.0
    opening = max(.05, 1 - .88 * blink - .16 * max(charge, flip))
    left = (
        '<path d="M144 265 Q178 242 224 259 L214 282 '
        'Q176 302 151 281Z" fill="#20372e" stroke="#183527" '
        'stroke-width="8" stroke-linejoin="round"/>'
        '<path d="M154 269 Q186 258 217 267 Q186 283 159 282Z" '
        'fill="#baffeb" stroke="#1a5341" stroke-width="4"/>'
        f'<path d="M{_n(185+hunt)} 266 Q{_n(191+hunt)} 274 {_n(186+hunt)} 284 '
        f'Q{_n(179+hunt)} 276 {_n(185+hunt)} 266Z" fill="#073b42"/>'
        f'<path d="M{_n(181+hunt)} 267 l-3 7" fill="none" stroke="#effff4" stroke-width="3"/>'
    )
    right = (
        '<path d="M284 259 Q322 232 363 249 L356 274 '
        'Q328 298 293 284Z" fill="#20372e" stroke="#183527" '
        'stroke-width="8" stroke-linejoin="round"/>'
        '<path d="M293 261 Q330 248 352 257 Q325 276 297 276Z" '
        'fill="#c9fff1" stroke="#1a5341" stroke-width="4"/>'
        f'<path d="M{_n(323+hunt*.65)} 258 Q{_n(329+hunt*.65)} 268 {_n(322+hunt*.65)} 279 '
        f'Q{_n(316+hunt*.65)} 268 {_n(323+hunt*.65)} 258Z" fill="#063d43"/>'
        f'<path d="M{_n(320+hunt*.65)} 259 l-3 6" fill="none" stroke="#effff4" stroke-width="3"/>'
    )
    if animation == "death":
        left = '<path d="M158 261 l57 22 m-48 4 l48 -27" fill="none" stroke="#173a30" stroke-width="13" stroke-linecap="round"/>'
        right = '<path d="M300 251 l49 28 m-51 0 l55 -27" fill="none" stroke="#173a30" stroke-width="13" stroke-linecap="round"/>'
        opening = 1.0
    elif animation == "hurt":
        left = '<path d="M154 273 Q181 250 215 270" fill="none" stroke="#244c37" stroke-width="14" stroke-linecap="round"/>'
        right = '<path d="M295 269 Q326 247 356 260" fill="none" stroke="#244c37" stroke-width="14" stroke-linecap="round"/>'
        opening = 1.0
    left = f'<g transform="translate(0 271) scale(1 {_n(opening)}) translate(0 -271)">{left}</g>'
    right = f'<g transform="translate(0 264) scale(1 {_n(opening)}) translate(0 -264)">{right}</g>'
    brows = (
        '<path d="M131 233 Q172 219 228 251 L220 266 Q178 249 143 250Z" '
        'fill="#35662c" stroke="#204927" stroke-width="5"/>'
        '<path d="M277 251 Q320 217 374 223 L366 241 '
        'Q324 240 291 265Z" fill="#35662c" stroke="#204927" stroke-width="5"/>'
    )
    return left, right, brows


def _mouth(progress: float, animation: str, charge: float, flip: float) -> str:
    # A vertical, collapsing singularity / cruel compressed grin rather than
    # a gnashing jaw. Small fang-like inward points make it hostile at 64px.
    wide = max(charge, flip * .75)
    if animation == "death":
        return (
            '<path d="M258 351 Q245 373 255 399 Q265 418 268 400 '
            'Q274 374 258 351Z" fill="#142c28" stroke="#245244" stroke-width="7"/>'
        )
    if animation == "hurt":
        return (
            '<path d="M226 368 Q256 350 297 365 Q280 388 257 386 '
            'Q234 385 226 368Z" fill="#1d292b" stroke="#22584c" stroke-width="8"/>'
            '<path d="M233 356 l-12 -13 M295 355 l14 -14" fill="none" '
            'stroke="#2b5c36" stroke-width="8" stroke-linecap="round"/>'
        )
    width = 23 + 18 * wide
    height = 29 + 29 * wide
    cx, cy = 263, 366
    maw = (
        f'<path d="M{_n(cx)} {_n(cy-height)} '
        f'Q{_n(cx+width*.28)} {_n(cy-height*.5)} {_n(cx+width)} {_n(cy)} '
        f'Q{_n(cx+width*.26)} {_n(cy+height*.33)} {_n(cx)} {_n(cy+height)} '
        f'Q{_n(cx-width*.26)} {_n(cy+height*.36)} {_n(cx-width)} {_n(cy)} '
        f'Q{_n(cx-width*.28)} {_n(cy-height*.5)} {_n(cx)} {_n(cy-height)}Z" '
        'fill="#101b1d" stroke="#234a39" stroke-width="10" stroke-linejoin="round"/>'
        f'<path d="M{_n(cx)} {_n(cy-height+8)} L{_n(cx+7)} {_n(cy)} '
        f'L{_n(cx)} {_n(cy+height-7)} L{_n(cx-7)} {_n(cy)}Z" '
        'fill="#7dfbef" opacity=".78"/>'
        '<path d="M189 352 L216 365 L235 359 M292 359 L316 368 L340 347" '
        'fill="none" stroke="#163b30" stroke-width="12" stroke-linecap="round" '
        'stroke-linejoin="round"/>'
        '<path d="M210 361 l15 5 -4 -15 M311 365 l8 -16 12 0" '
        'fill="none" stroke="#b2e2a5" stroke-width="5" stroke-linejoin="round"/>'
        '<path d="M247 319 l8 11 M279 321 l-7 10 M254 410 l-7 10" '
        'fill="none" stroke="#316c51" stroke-width="5" stroke-linecap="round" opacity=".78"/>'
    )
    return maw


def _fruit_parts(body_path: str, progress: float, animation: str, charge: float, flip: float) -> list[Part]:
    attached = lambda artwork: _attached(artwork)
    apple = (
        f'<path d="{body_path}" fill="url(#green-apple)" '
        'stroke="#223925" stroke-width="12" stroke-linejoin="round"/>'
        '<g clip-path="url(#apple-cut)">'
        '<ellipse cx="159" cy="226" rx="196" ry="223" fill="url(#apple-sun)"/>'
        '<path d="M118 185 Q161 149 198 163" fill="none" '
        'stroke="#f4ffb5" stroke-width="15" stroke-linecap="round" opacity=".29"/>'
        '<path d="M378 267 Q401 328 372 389" fill="none" '
        'stroke="#244e2e" stroke-width="10" stroke-linecap="round" opacity=".23"/>'
        '</g>'
    )
    axis = (
        '<path d="M254 177 L269 195 L255 214 L241 195Z" '
        'fill="#c0fff2" stroke="#297765" stroke-width="6" stroke-linejoin="round"/>'
        '<path d="M255 185 l6 10 -6 10 -6 -10Z" fill="#287468"/>'
        '<path d="M255 219 v15 M255 411 v12" fill="none" stroke="#c9ffe2" '
        'stroke-width="8" stroke-linecap="round" opacity=".7"/>'
    )
    equator = (
        '<g clip-path="url(#apple-cut)">'
        '<path d="M91 313 Q145 296 198 304" fill="none" '
        'stroke="#b6fff4" stroke-width="9" opacity=".5"/>'
        '<path d="M316 308 Q368 286 416 298" fill="none" '
        'stroke="#b6fff4" stroke-width="9" opacity=".5"/>'
        '<path d="M110 343 Q163 334 201 339 M315 335 Q362 324 394 326" '
        'fill="none" stroke="#529579" stroke-width="6" opacity=".55"/>'
        '</g>'
    )
    left_eye, right_eye, brow = _eyes(progress, animation, charge, flip)
    stem = (
        '<path d="M251 143 Q248 111 262 91" fill="none" '
        'stroke="#4a3d25" stroke-width="21" stroke-linecap="round"/>'
        '<path d="M253 143 Q252 112 262 93" fill="none" '
        'stroke="#a57c45" stroke-width="9" stroke-linecap="round"/>'
    )
    motion = math.sin(progress * math.tau)
    # Independent fins pivot at their roots. This is local calyx motion, not a
    # precooked rolling pose or a velocity trail.
    left_angle = -5 + 9 * motion - 6 * charge
    right_angle = 7 - 7 * motion + 7 * charge
    fin_l = (
        '<path d="M251 144 Q207 108 157 112 Q165 147 191 164 '
        'Q216 173 257 159Z" fill="url(#leaf-green)" '
        'stroke="#24452b" stroke-width="12" stroke-linejoin="round"/>'
        '<path d="M246 150 Q203 130 173 126" fill="none" '
        'stroke="#cbf487" stroke-width="7" stroke-linecap="round"/>'
    )
    fin_r = (
        '<path d="M256 148 Q305 87 370 94 Q356 136 330 154 '
        'Q305 171 255 160Z" fill="url(#leaf-green)" '
        'stroke="#24452b" stroke-width="12" stroke-linejoin="round"/>'
        '<path d="M269 146 Q315 114 355 110" fill="none" '
        'stroke="#d5f8a6" stroke-width="7" stroke-linecap="round"/>'
    )
    # Pivots are expressed in the assembled 512-unit canvas, not the 512-unit
    # apple art before its 0.68x reduction. This matters for exported parts.
    def pivot(x: float, y: float) -> tuple[int, int]:
        return (round(82 + .68 * x), round(36 + .68 * y))

    return [
        Part("apple_body", "fruit", 10, pivot(256, 254), attached(apple)),
        Part("gravity_axis", "fruit", 12, pivot(255, 195), attached(axis)),
        Part("equator_marks", "fruit", 14, pivot(256, 320), attached(equator)),
        Part("eyebrows", "face", 23, pivot(256, 238), attached(brow)),
        Part("eye_left", "face", 24, pivot(185, 271), attached(left_eye)),
        Part("eye_right", "face", 24, pivot(323, 264), attached(right_eye)),
        Part("singularity_mouth", "face", 26, pivot(263, 366), attached(_mouth(progress, animation, charge, flip))),
        Part("stem", "stem", 31, pivot(252, 143), attached(stem)),
        Part("fin_left", "calyx", 32, pivot(251, 153), _attached(fin_l, local_transform=f"rotate({_n(left_angle)} 251 153)")),
        Part("fin_right", "calyx", 33, pivot(256, 153), _attached(fin_r, local_transform=f"rotate({_n(right_angle)} 256 153)")),
    ]


def parts(animation: str, frame: int, count: int, *, body_path: str) -> list[Part]:
    if count <= 0 or not (0 <= frame < count):
        raise ValueError("frame must be within the animation")
    if animation not in {"idle", "float", "charge", "flip", "hurt", "death"}:
        raise ValueError(f"unsupported Gravity Apple animation: {animation}")
    progress = frame / max(1, count - 1)
    charge = _pulse(progress) if animation == "charge" else 0.0
    flip = _pulse(progress) if animation == "flip" else 0.0
    all_parts = _orbit_parts(progress, animation, charge) + _fruit_parts(body_path, progress, animation, charge, flip)
    return sorted(all_parts, key=lambda p: (p.z, p.name))


def _pose(animation: str, frame: int, count: int) -> str:
    # The root can translate and deform but never rotates. The game should
    # apply a physically interpolated roll to the whole assembled character.
    t = frame / count * math.tau
    progress = frame / max(1, count - 1)
    charge = _pulse(progress) if animation == "charge" else 0
    y = -12 + 5 * math.sin(t)
    sx, sy = 1 + .015 * math.sin(t), 1 - .015 * math.sin(t)
    if animation == "charge":
        sx += .045 * charge
        sy -= .035 * charge
    elif animation == "hurt":
        sx, sy = .96, 1.04
    elif animation == "death":
        sx += .14 * progress
        sy -= .29 * progress
        y += 9 * progress
    return f'translate(256 {_n(254+y)}) scale({_n(sx)} {_n(sy)}) translate(-256 -254)'


def frame_svg(
    animation: str,
    frame: int,
    count: int,
    *,
    body_path: str,
    only_part: str | None = None,
) -> str:
    elements = parts(animation, frame, count, body_path=body_path)
    if only_part is not None:
        elements = [part for part in elements if part.name == only_part]
        if not elements:
            raise ValueError(f"unknown Gravity Apple part: {only_part}")
    content = "".join(part.svg_group() for part in elements)
    return (
        SVG_START[:-1]
        + f' aria-label="gravity apple {animation} sprite">'
        + _defs(body_path)
        + f'<g id="character_pose" data-rig-part="character_pose" '
        f'data-rig-bone="root" transform="{_pose(animation, frame, count)}">'
        + content + '</g></svg>'
    )
