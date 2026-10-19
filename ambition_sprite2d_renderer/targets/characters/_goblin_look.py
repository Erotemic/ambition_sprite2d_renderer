"""How a goblin looks: the parts ``goblin_side`` places on its skeleton.

A LOOK is the drawing of one goblin: its head and torso shapes, its outfit,
eyes, weapon style, hats and gear, palette, and its size. The skeleton and
the moves are the goblin's (``goblin_side``, ``_goblin_moves``) and every
look wears them; a look may move the head and shoulders on the body
(``layout``) and scale the whole figure about its feet (``k``) on a canvas
``canvas`` times the goblin's 128-unit frame (its config's ``frame_width``
must be ``128 * canvas``).

Each part is painted once, in its own frame and in design units (the
goblin's 128-unit frame; the head faces +x), as two rasters: its INK, the
silhouette grown by the outline, and its shaded FILL. A limb places both
segments' inks before their fills, so a joint reads as one outline; every
other part is one raster, its fill over its ink.

Looks (Jon, 2026-10-18): ``classic`` is the Smash goblin's default;
``raider`` and ``squat`` are its other two skins; ``brute`` (the Goblin
Brute) and ``bruiser`` are heavies, drawn bigger; ``fretjaw`` is the cantina
chieftain; ``bard`` is a goblin of his band.
"""

from __future__ import annotations

import math
from typing import Callable, Dict, List, Optional, Tuple

from PIL import Image, ImageChops, ImageDraw

from ...authoring import shape_rig
from ...core.draw import blending_draw, rgba

Point = Tuple[float, float]
Color = Tuple[int, int, int, int]
H = rgba


def smooth(pts, n: int = 6) -> List[Point]:
    """A closed Catmull-Rom curve through ``pts``; a point with a third
    element ``True`` is a corner."""
    out: List[Point] = []
    m = len(pts)
    for i in range(m):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % m], pts[(i + 2) % m]
        if len(p1) > 2 and p1[2]:
            p0 = p1
        if len(p2) > 2 and p2[2]:
            p3 = p2
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(
                0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                       + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    return out


def scaled(pts, k: float, about: Point = (0.0, 0.0)):
    """``pts`` scaled by ``k`` about ``about``, corner flags kept."""
    return [tuple([about[0] + (q[0] - about[0]) * k, about[1] + (q[1] - about[1]) * k] + list(q[2:])) for q in pts]


def taper(length: float, r0: float, r1: float) -> List[tuple]:
    """A limb segment along +x: a round end of radius ``r0`` at the joint and
    ``r1`` at ``length``."""
    pts = []
    for k in range(7):
        t = math.pi / 2 + k * math.pi / 6
        pts.append((r0 * math.cos(t), r0 * math.sin(t)))
    for k in range(7):
        t = -math.pi / 2 + k * math.pi / 6
        pts.append((length + r1 * math.cos(t), r1 * math.sin(t)))
    return pts


class Part:
    """One part's local canvas: ink and fill rasters, shapes in design units
    about ``(0, 0)``, ``half`` units each way."""

    def __init__(self, S: float, half: float):
        self.S, self.half = S, half
        n = int(math.ceil(2 * half * S))
        self.ink = Image.new("RGBA", (n, n), (0, 0, 0, 0))
        self.fill = Image.new("RGBA", (n, n), (0, 0, 0, 0))
        self.di, self.df = blending_draw(self.ink), blending_draw(self.fill)

    def P(self, pts):
        S, h = self.S, self.half
        return [((q[0] + h) * S, (q[1] + h) * S) for q in pts]

    def mask(self, pts) -> Image.Image:
        m = Image.new("L", self.fill.size, 0)
        ImageDraw.Draw(m).polygon(self.P(pts), fill=255)  # raw-draw-ok: an L coverage mask, not content
        return m

    def shape(self, pts, fill, ink, ow, *, shade=None, light=None, d=(2.2, 2.6), corner_n=6) -> None:
        """A smooth shape: its ink, its fill, a ``shade`` band along the edge
        away from the light (up and back) and a ``light`` band toward it."""
        sm = smooth(pts, corner_n)
        P = self.P(sm)
        self.di.polygon(P, fill=ink)
        self.di.line(P + [P[0]], fill=ink, width=max(1, int(round(2 * ow * self.S))), joint="curve")
        self.df.polygon(P, fill=fill)
        self.tone(sm, shade, d)
        if light is not None:
            self.tone(sm, light, (-d[0] * 0.6, -d[1] * 0.6))

    def tone(self, sm, color, d) -> None:
        """``color`` over the band of ``sm`` that moving by ``d`` leaves."""
        if color is None:
            return
        m = self.mask(sm)
        moved = ImageChops.offset(m, -int(round(d[0] * self.S)), -int(round(d[1] * self.S)))
        self.fill.paste(Image.new("RGBA", self.fill.size, color), (0, 0), ImageChops.subtract(m, moved))

    def inner(self, pts, color, clip=None, n=6, corner=False) -> None:
        """A flat shape on the fill alone, clipped to the shape ``clip``."""
        sm = pts if corner else smooth(pts, n)
        if clip is None:
            self.df.polygon(self.P(sm), fill=color)
            return
        m = ImageChops.multiply(self.mask(sm), self.mask(smooth(clip)))
        self.fill.paste(Image.new("RGBA", self.fill.size, color), (0, 0), m)

    def line(self, pts, color, w) -> None:
        self.df.line(self.P(pts), fill=color, width=max(1, int(round(w * self.S))), joint="curve")

    def ellipse(self, c, r, color, ink=None, ow=0.0) -> None:
        S, h = self.S, self.half
        box = ((c[0] - r[0] + h) * S, (c[1] - r[1] + h) * S, (c[0] + r[0] + h) * S, (c[1] + r[1] + h) * S)
        if ink is not None:
            g = ow * S
            self.di.ellipse((box[0] - g, box[1] - g, box[2] + g, box[3] + g), fill=ink)
        self.df.ellipse(box, fill=color)

    def arc(self, c, r, start, end, color, w) -> None:
        S, h = self.S, self.half
        box = ((c[0] - r + h) * S, (c[1] - r + h) * S, (c[0] + r + h) * S, (c[1] + r + h) * S)
        self.df.arc(box, start, end, fill=color, width=max(1, int(round(w * S))))

    def pivot(self) -> Point:
        return (self.half * self.S, self.half * self.S)

    def split(self):
        """(ink piece, fill piece), for a part whose joint blends."""
        return (self.ink, self.pivot()), (self.fill, self.pivot())

    def merged(self):
        """One piece: the fill over the ink."""
        out = self.ink.copy()
        out.alpha_composite(self.fill)
        return (out, self.pivot())


def piece(key: tuple, half: float, S: float, paint: Callable[[Part], None], split: bool = False):
    """The part ``paint`` paints, cached by ``key`` (which names everything
    ``paint`` reads) and the scale."""
    k = ("goblin_look",) + tuple(key) + (round(S, 4), split)
    cached = shape_rig._PIECES.get(k)
    if cached is None:
        part = Part(S, half)
        paint(part)
        cached = part.split() if split else part.merged()
        shape_rig._PIECES[k] = cached
    return cached


# --- palettes ------------------------------------------------------------------------------

#: Every key a look's palette names.
CLASSIC = dict(
    ink=H("#1B2412"), skin=H("#6FAE4E"), skin_lt=H("#9ED36F"), skin_sh=H("#4C8636"), skin_far=H("#4F8A39"),
    skin_far_sh=H("#3B6B2A"), belly=H("#8CC466"), ear_in=H("#C9739A"), cloth=H("#6D2BA0"), cloth_sh=H("#4B1E72"),
    cloth_lt=H("#8B4BC0"), eye=H("#F24DFF"), eye_glow=H("#FFD0FF"), sclera=H("#F6E7B8"), mouth=H("#2A1B18"),
    tooth=H("#F4EBD5"), grip=H("#6A2CC1"), metal=H("#D9DCE4"), metal_sh=H("#9AA0AE"), metal_lt=H("#FFFFFF"),
    leather=H("#5B3A26"), nail=H("#E8E2C8"), belt=H("#3B2A1E"), buckle=H("#C9A646"), wood=H("#8A5A33"),
    wood_sh=H("#5E3B20"), wood_lt=H("#A87445"), bone=H("#EDE3C6"), bone_sh=H("#C9BD9C"), gold=H("#E3B23C"),
    gold_sh=H("#A87A1E"), iron=H("#6F747C"), iron_sh=H("#4A4E55"), iron_lt=H("#9BA1AA"), rust=H("#8A5A33"),
    shirt=H("#EADDBE"), shirt_sh=H("#C9B994"), apron=H("#F0E6CF"), apron_sh=H("#CDBF9E"), wrap=H("#E4D9BE"),
    wrap_sh=H("#B5A989"), rope=H("#B59A63"), stone=H("#9B9384"), stone_sh=H("#6F685C"), stone_lt=H("#BDB6A6"),
)


def palette(**changes) -> Dict[str, Color]:
    out = dict(CLASSIC)
    out.update({k: H(v) if isinstance(v, str) else v for k, v in changes.items()})
    return out


def _skin(skin, lt, sh, far, far_sh, belly, ink):
    return dict(skin=skin, skin_lt=lt, skin_sh=sh, skin_far=far, skin_far_sh=far_sh, belly=belly, ink=ink)


# --- shapes ----------------------------------------------------------------------------------

HEADS = {
    "round": dict(
        cran=[(-14, 1), (-12, -8), (-4, -12.5), (6, -11.5), (12, -6), (14, 0), (12, 7), (4, 11), (-6, 10.5), (-12, 7)],
        nose=[(11, -3), (19, 1, True), (13, 5), (10, 3)],
        ear=[(-6, -6), (-18, -11), (-34, -14, True), (-20, -3), (-9, 3)],
        ear_in=[(-10, -4.5), (-19, -8), (-29, -11.5, True), (-19, -4), (-11, 0)],
        far_ear=[(-3, -9), (-15, -16), (-29, -21, True), (-15, -9), (-6, -4)],
        eye=(6.5, -3.0), mouth=((6, 6), (15, 5)), fangs=(2.4, 2.0)),
    "hook": dict(
        cran=[(-13, 0), (-11.5, -8), (-4, -12.5), (5, -12), (10.5, -7), (12, -3), (11, 1), (12.5, 5), (8, 10), (0, 11), (-8, 9), (-12, 5)],
        nose=[(9.5, -5), (15, -2), (21, 4, True), (17, 5.5), (12.5, 3.5), (10, 1)],
        ear=[(-5, -7), (-16, -11), (-34, -16, True), (-22, -5), (-10, 3), (-6, 1)],
        ear_in=[(-9, -5), (-17, -8.5), (-29, -13, True), (-19, -5), (-11, 0)],
        far_ear=[(-2, -9), (-12, -17), (-27, -24, True), (-16, -11), (-6, -5)],
        eye=(5.5, -3.5), mouth=((4, 6.5), (13.5, 6)), fangs=(2.4, 2.0)),
    "bulb": dict(
        cran=[(-13, -1), (-11, -9), (-3, -12.5), (6, -11), (11, -6), (12, -1), (16, 3), (17, 8), (12, 12.5), (2, 12.5), (-7, 10), (-12, 5)],
        nose=[(11, -3), (16.5, -3.5), (19, 0.5), (16, 3.5), (11.5, 2.5)],
        ear=[(-6, -5), (-18, -6), (-31, 2, True), (-19, 4), (-9, 4)],
        ear_in=[(-10, -3), (-19, -3.5), (-27, 1.5, True), (-18, 2), (-11, 1.5)],
        far_ear=[(-3, -8), (-16, -12), (-29, -8, True), (-15, -3), (-6, -2)],
        eye=(4.5, -4.0), mouth=((5, 7.5), (16, 6.5)), fangs=(2.4, 2.0)),
    # The heavy: a low skull, a slab of a jaw and tusks, short ears.
    "brute": dict(
        cran=[(-12, 0), (-10, -8), (-2, -11), (7, -9.5), (12, -5), (13, -1), (17, 3), (17.5, 9), (12, 13.5), (1, 13.5), (-8, 11), (-12, 5)],
        nose=[(11, -3.5), (16.5, -2.5), (18, 1.2), (14.5, 3), (11, 2)],
        ear=[(-6, -5), (-15, -8), (-25, -10, True), (-17, -1), (-9, 3)],
        ear_in=[(-9.5, -3.5), (-16, -6), (-22, -7.5, True), (-16, -1.5), (-11, 0.5)],
        far_ear=[(-3, -8), (-12, -13), (-21, -16, True), (-13, -6), (-6, -3)],
        eye=(5.0, -4.2), mouth=((5, 8.5), (17, 7.5)), fangs=(4.2, 3.6)),
    # Fretjaw: jowls, a big droopy nose, long ears hanging out to the side.
    "host": dict(
        cran=[(-13, 0), (-11, -8), (-3, -12.5), (6, -11.5), (11, -6), (12, -1), (14, 4), (12, 10.5), (4, 12.5), (-6, 11), (-12, 6)],
        nose=[(9.5, -4.5), (15.5, -3), (20, 2), (18.5, 6.5), (13.5, 6.5), (10, 2.5)],
        ear=[(-6, -6), (-18, -8), (-34, -3, True), (-20, 2), (-9, 4)],
        ear_in=[(-10, -4), (-19, -5.5), (-30, -2.5, True), (-19, 0), (-11, 1)],
        far_ear=[(-3, -9), (-15, -13), (-30, -12, True), (-15, -5), (-6, -4)],
        eye=(5.5, -4.0), mouth=((4, 8.5), (13.5, 8.5)), fangs=(0.0, 0.0)),
}

TORSOS = {
    "round": [(-11, 0), (-9, -8), (0, -11), (9, -8), (12, 0), (10, 8), (2, 11), (-7, 10)],
    "lean": [(-11, 2), (-10, -6), (-5, -11), (3, -11.5), (10, -8), (12, -2), (12.5, 5), (7, 11), (-4, 11.5), (-10, 8)],
    "pot": [(-11, 1), (-9, -7), (-2, -10.5), (7, -9), (12, -3), (14, 5), (10, 11.5), (0, 12.5), (-8, 10)],
    # The heavy: a hump of shoulders over a barrel.
    "barrel": [(-13, 4), (-14, -5), (-10, -13), (-1, -16.5), (9, -14.5), (15, -8), (16, 1), (14, 9), (7, 13), (-4, 13.5), (-11, 10)],
}


# --- looks -----------------------------------------------------------------------------------

LOOKS: Dict[str, dict] = {}


def look(name: str, **kw) -> None:
    kw.update(name=name)
    for key, value in (("k", 1.0), ("limb", 1.0), ("head_scale", 1.0), ("hats", ()), ("gear", ()),
                       ("canvas", 1.0), ("sleeve", None), ("layout", {}), ("hammer", "maul"), ("eye", "beady")):
        kw.setdefault(key, value)
    LOOKS[name] = kw


look("classic", pal=palette(), head="round", torso="round", outfit="loincloth", eye="glow", sword="clean")
look("raider", head="hook", torso="lean", outfit="tunic", sword="rusty", pal=palette(
    **_skin(H("#8E9F4C"), H("#AEBE66"), H("#6B7A36"), H("#6E7D3A"), H("#56632C"), H("#9FAE5C"), H("#1E1F14")),
    ear_in="#B5786B", cloth="#7B5233", cloth_sh="#5A3A23", cloth_lt="#97693F", eye="#F4D03F", eye_glow="#FFF4B8",
    sclera="#F4D03F", mouth="#2A1A14", tooth="#EFE5C8", grip="#4A3122", metal="#B9B8AD", metal_sh="#7D7C72",
    metal_lt="#E2E1D6", leather="#4A3122", nail="#D9CFAE"))
look("squat", head="bulb", torso="pot", outfit="hide", sword="jagged", pal=palette(
    **_skin(H("#7E9474"), H("#A0B694"), H("#5D7156"), H("#627759"), H("#4C5E45"), H("#9DAE8A"), H("#1A1D17")),
    ear_in="#B87C7C", cloth="#8C6A4A", cloth_sh="#6A4E35", cloth_lt="#A5835F", eye="#E5483A", eye_glow="#FFC0B0",
    sclera="#F2E3B5", mouth="#2A1715", tooth="#F1E6C6", grip="#3E2C20", metal="#C2C4BD", metal_sh="#82857D",
    metal_lt="#ECEDE6", leather="#3E2C20", nail="#DCD3B5", belt="#3E2C20"))
# The heavies: a hunched barrel of a body, a small low head, thick limbs.
HEAVY = dict(head="brute", torso="barrel", outfit="kilt", k=1.32, head_scale=0.92, canvas=1.375,
             layout=dict(head_at=(17.0, -24.0), shoulders={"far": (-9.0, -11.0), "near": (8.0, -11.0)}))
look("brute", **HEAVY, hammer="maul", limb=1.55, hats=("iron_cap",), gear=("pauldron", "harness"),
     pal=palette(**_skin(H("#7B8F3F"), H("#9DB25A"), H("#59692B"), H("#5D6D2E"), H("#475424"), H("#8DA04E"), H("#1C1F12")),
                 ear_in="#A86F5E", cloth="#7A3A2A", cloth_sh="#55271C", cloth_lt="#954C38", eye="#FF7A3D",
                 eye_glow="#FFD9B8", sclera="#F2D9A6", mouth="#28160F", tooth="#F0E3C2", grip="#4B3222",
                 leather="#4B3222", nail="#D7CBA8"))
look("bruiser", **HEAVY, hammer="club", limb=1.6, hats=("nose_ring",), gear=("wraps", "rope"),
     pal=palette(**_skin(H("#7F8C6C"), H("#A0AD8A"), H("#5E6A4E"), H("#636F52"), H("#4D573F"), H("#95A07D"), H("#1C1F12")),
                 ear_in="#A86F5E", cloth="#5A5048", cloth_sh="#3F3832", cloth_lt="#71665C", eye="#F2C14E",
                 eye_glow="#FFF0B8", sclera="#F2D9A6", mouth="#28160F", tooth="#F0E3C2", grip="#4B3222",
                 leather="#4B3222", nail="#D7CBA8"))
# Fretjaw, the cantina chieftain, and a bard of his band.
FRETJAW = dict(**_skin(H("#79A44A"), H("#A3CB68"), H("#567A33"), H("#5B8236"), H("#46662A"), H("#93BC5E"), H("#1D2113")),
               ear_in="#C7806E", cloth="#D0702E", cloth_sh="#9A4C1C", cloth_lt="#E58C48", eye="#FFC233",
               eye_glow="#FFF0B0", mouth="#2B1712")
look("fretjaw", head="host", torso="pot", outfit="host", hammer="gavel", k=1.08, limb=1.1,
     hats=("caps_crown", "earring", "mustache"), canvas=1.125, sleeve="shirt", pal=palette(**FRETJAW))
look("bard", head="host", torso="pot", outfit="bard", hammer="gavel", k=1.08, limb=1.1,
     hats=("plumed_hat", "earring"), gear=("lute",), canvas=1.125,
     pal=palette(**dict(FRETJAW, cloth="#B0352B", cloth_sh="#7E241D", cloth_lt="#C9533F", shirt="#6E5134", shirt_sh="#4F3924")))
# The hall's other goblins: the classic build in their own colours and kit.
look("forest", head="round", torso="round", outfit="loincloth", hats=("hood",), pal=palette(
    **_skin(H("#5C9248"), H("#8CC66B"), H("#345B2A"), H("#447536"), H("#2E5025"), H("#74AA58"), H("#172312")),
    cloth="#6B4F2E", cloth_sh="#4A361E", cloth_lt="#87683F", eye="#EF52FF", eye_glow="#F6BCFF"))
look("cave", head="bulb", torso="round", outfit="loincloth", hats=("bandana",), sword="jagged", pal=palette(
    **_skin(H("#5F6F68"), H("#8EA29A"), H("#35423E"), H("#4A5A53"), H("#36433E"), H("#778A82"), H("#15191A")),
    ear_in="#9B7A86", cloth="#394BA0", cloth_sh="#242C69", cloth_lt="#5266BE", eye="#6BE9FF", eye_glow="#D9FFFF"))
look("desert", head="hook", torso="lean", outfit="loincloth", hats=("headwrap",), pal=palette(
    **_skin(H("#A7A34B"), H("#D4C76B"), H("#67632B"), H("#87843B"), H("#5E5A27"), H("#BDB65D"), H("#221F10")),
    ear_in="#C98B6B", cloth="#B06B2A", cloth_sh="#72451D", cloth_lt="#CC8540", eye="#FF7059", eye_glow="#FFD0C7",
    sclera="#FF7059"))
look("frost", head="round", torso="round", outfit="loincloth", hats=("scarf",), pal=palette(
    **_skin(H("#6EA0A3"), H("#A8DDE0"), H("#3B686B"), H("#558487"), H("#3B5F61"), H("#85BFC0"), H("#14201F")),
    ear_in="#B98AA4", cloth="#5063B8", cloth_sh="#2B3677", cloth_lt="#6A7ED0", eye="#FFFFFF", eye_glow="#B6FFF5",
    metal="#E2F6FA"))
look("shaman", head="hook", torso="round", outfit="loincloth", hats=("feathers",), pal=palette(
    **_skin(H("#4C8A5B"), H("#78C987"), H("#2E5D37"), H("#3C6F48"), H("#2A5032"), H("#6BAB73"), H("#142116")),
    cloth="#7E4FCC", cloth_sh="#4C2C87", cloth_lt="#9A6EE0", eye="#FFE36E", eye_glow="#FFF6B0", sclera="#FFE36E"))

#: Archetype tokens to looks, first match wins (``build_spec``).
ARCHETYPE_LOOKS = [
    ("chieftain", "fretjaw"), ("chief", "fretjaw"), ("brute", "brute"), ("bruiser", "bruiser"), ("raider", "raider"),
    ("squat", "squat"), ("shaman", "shaman"), ("bard", "bard"), ("drummer", "bard"), ("cave", "cave"), ("desert", "desert"),
    ("frost", "frost"), ("scout", "forest"), ("forest", "forest"),
]


def look_for_archetype(archetype: Optional[str]) -> str:
    key = str(archetype or "default").lower()
    for token, name in ARCHETYPE_LOOKS:
        if token in key:
            return name
    return "classic" if key == "default" else "forest"


# --- painting ----------------------------------------------------------------------------------

OW = 0.95


class Painter:
    """The parts of one look."""

    def __init__(self, look_name: str):
        self.L = LOOKS[look_name]
        self.pal = self.L["pal"]

    def key(self, *rest) -> tuple:
        return (self.L["name"],) + rest

    # -- limbs ----------------------------------------------------------------------------
    def segment(self, S, length, r0, r1, fill, shade, wraps=False):
        """A limb segment, split (ink, fill) so its joint blends."""
        pal = self.pal

        def paint(p: Part):
            shape = taper(length, r0, r1)
            p.shape(shape, fill, pal["ink"], OW, shade=shade, d=(0.0, 1.1 * self.L["limb"]), corner_n=2)
            if wraps:
                for i in range(4):
                    x = length * (0.35 + 0.15 * i)
                    r = r0 + (r1 - r0) * x / length
                    p.inner([(x - 1.2, -r - 0.2), (x + 1.0, -r - 0.2), (x + 1.8, r + 0.2), (x - 0.4, r + 0.2)], pal["wrap"], corner=True, clip=shape)
                    p.line([(x + 1.0, -r), (x + 1.8, r)], pal["wrap_sh"], 0.35)

        return piece(self.key("seg", round(length, 2), round(r0, 3), round(r1, 3), fill, shade, wraps), length + r0 + 3, S, paint, split=True)

    # -- head -----------------------------------------------------------------------------
    def head(self, S, blink: bool, squint: float, dead: bool, mouth: float):
        return piece(self.key("head", blink, squint, dead, mouth), 44, S, lambda p: self._paint_head(p, blink, squint, dead, mouth))

    def far_ear(self, S):
        g = self._head_geometry()
        return piece(self.key("far_ear"), 44, S, lambda p: p.shape(g["far_ear"], self.pal["skin_far"], self.pal["ink"], OW, shade=self.pal["skin_far_sh"]))

    def _head_geometry(self):
        hs = self.L["head_scale"]
        return {k: (scaled(v, hs) if isinstance(v, list) else v) for k, v in HEADS[self.L["head"]].items()}

    def _paint_head(self, p: Part, blink, squint, dead, mouth) -> None:
        pal, ink, L = self.pal, self.pal["ink"], self.L
        g, hs, kind = self._head_geometry(), L["head_scale"], L["head"]
        if "hood" in L["hats"]:
            self._paint_hat(p, "hood_back", g)
        p.shape(g["ear"], pal["skin"], ink, OW, shade=pal["skin_sh"], light=pal["skin_lt"])
        p.inner(g["ear_in"], pal["ear_in"])
        if "earring" in L["hats"]:
            tip, back = g["ear"][2], g["ear"][3]
            c = (tip[0] * 0.55 + back[0] * 0.45, tip[1] * 0.55 + back[1] * 0.45 + 2.0)
            p.ellipse(c, (1.9, 1.9), pal["gold"], ink, 0.5)
            p.ellipse(c, (1.0, 1.0), (0, 0, 0, 0))
        p.shape(g["cran"], pal["skin"], ink, OW, shade=pal["skin_sh"], light=pal["skin_lt"], d=(2.6, 3.0))
        p.shape(g["nose"], pal["skin"], ink, OW, shade=pal["skin_sh"], light=pal["skin_lt"] if kind in ("bulb", "host", "brute") else None, d=(1.2, 1.5))
        ex, ey = g["eye"][0] * hs, g["eye"][1] * hs
        if dead:
            for s in (-1, 1):
                p.line([(ex - 2, ey - 2 * s), (ex + 2, ey + 2 * s)], ink, 0.9)
        elif blink:
            p.line([(ex - 2.6, ey + 0.3), (ex + 2.4, ey)], ink, 0.9)
        else:
            open_ = max(0.35, 1.0 - 0.55 * squint)
            if L["eye"] == "glow":
                p.ellipse((ex, ey), (2.6, 3.6 * open_), pal["eye"], ink, 0.5)
                p.ellipse((ex + 0.6, ey - 1.0 * open_), (0.8, 1.0 * open_), pal["eye_glow"])
            else:
                r = 2.3 if kind == "brute" else 2.9
                p.ellipse((ex, ey), (r, r * 0.83 * open_), pal["sclera"], ink, 0.5)
                p.ellipse((ex + 1.0, ey), (1.2, 1.4 * open_), ink)
                p.ellipse((ex + 0.6, ey - 0.6), (0.4, 0.4), pal["eye_glow"])
        # A heavy brow slanting down to the nose: the scowl.
        bx, by = ex, ey - 3.6 + (0.8 if squint > 0.3 else 0.0)
        heavy = 1.6 if kind == "brute" else 1.0
        p.inner([(bx - 4.5, by - 1.0 * heavy), (bx + 0.5, by - 1.4 * heavy), (bx + 4.5, by + 0.6, True), (bx + 4, by + 1.6), (bx - 4.5, by + 0.6)], pal["skin_sh"])
        p.line([(bx - 4.2, by - 0.4), (bx + 4.4, by + 1.2)], ink, 0.85 * heavy)
        self._paint_mouth(p, g, hs, kind, mouth)
        if "mustache" in L["hats"]:
            nx, ny = 13.0, 6.8
            for side in (-1, 1):
                pts = [(nx, ny - 0.8), (nx + side * 4.5, ny - 0.2), (nx + side * 7.5, ny - 2.6, True), (nx + side * 6.5, ny + 1.2), (nx + side * 2.0, ny + 1.4)]
                p.shape(pts, H("#3A2A1C"), ink, OW * 0.6, corner_n=4)
        for hat in L["hats"]:
            self._paint_hat(p, hat, g)

    def _paint_mouth(self, p: Part, g, hs, kind, mouth) -> None:
        pal, ink = self.pal, self.pal["ink"]
        (ax, ay), (cx, cy) = [(q[0] * hs, q[1] * hs) for q in g["mouth"]]
        if mouth > 0.0:
            drop = 2.5 + 4.0 * mouth
            jaw = [(ax - 0.5, ay - 0.5), (cx + 0.5, cy - 0.8), (cx - 1.0, cy + drop, True), (ax + 1, ay + drop * 0.7)]
            p.shape(jaw, pal["mouth"], ink, OW * 0.7, corner_n=3)
            for tx in (ax + 2, cx - 3):
                p.inner([(tx - 0.8, ay - 0.2), (tx + 0.8, ay - 0.2), (tx, ay + 2.0)], pal["tooth"], corner=True)
            if kind == "host":
                p.inner([(ax + 4.2, ay - 0.1), (ax + 5.8, ay - 0.1), (ax + 5.0, ay + 2.2)], pal["gold"], corner=True)
            p.inner([(cx - 2.6, cy + drop - 0.2), (cx - 1.0, cy + drop - 0.4), (cx - 1.8, cy + drop - 2.4)], pal["tooth"], corner=True)
            return
        if kind == "host":
            # A showman's grin with a gold tooth.
            mid = ((ax + cx) / 2, (ay + cy) / 2 + 2.0)
            p.shape([(ax, ay - 0.6), (cx + 0.8, cy - 1.6, True), mid], pal["mouth"], ink, OW * 0.6, corner_n=4)
            p.inner([(ax + 2.5, ay - 0.3), (cx - 0.5, cy - 1.2), (cx - 1.5, cy + 0.2), (ax + 3.0, ay + 0.6)], pal["tooth"], corner=True)
            p.inner([(ax + 5.5, ay - 0.1), (ax + 7.0, ay - 0.3), (ax + 7.0, ay + 0.8), (ax + 5.5, ay + 0.9)], pal["gold"], corner=True)
            return
        mid = ((ax + cx) / 2, (ay + cy) / 2 + 0.9)
        p.line([(ax, ay), mid, (cx, cy)], ink, 0.85)
        # Underbite fangs over the lip.
        for tx, h in ((ax + 2.2, g["fangs"][0]), (cx - 2.0, g["fangs"][1])):
            ty = ay + (cy - ay) * ((tx - ax) / (cx - ax)) + 0.6
            w = 0.9 if h < 3 else 1.4
            pts = [(tx - w, ty + 0.4), (tx + w, ty + 0.4), (tx + 0.3, ty - h)]
            p.inner(pts, pal["tooth"], corner=True)
            p.line(pts + [pts[0]], ink, 0.45)
        if "nose_ring" in self.L["hats"]:
            p.arc((16.0 * hs, 2.8 * hs), 2.0, 300, 200, pal["gold"], 0.9)

    def _paint_hat(self, p: Part, hat: str, g) -> None:
        pal, ink = self.pal, self.pal["ink"]
        if hat == "iron_cap":
            cap = [(-11.5, -4), (-10, -10), (-2, -12.8), (7, -11), (11.5, -6), (12, -3.5), (0, -5.5)]
            p.shape(cap, pal["iron"], ink, OW, shade=pal["iron_sh"], light=pal["iron_lt"], d=(1.4, 1.6))
            p.line([(-11, -4.4), (0, -5.6), (12, -3.8)], pal["iron_sh"], 0.8)
            for x in (-7.5, -1.5, 5):
                p.ellipse((x, -6.4 + (0.3 if x > 0 else 0)), (0.7, 0.7), pal["iron_lt"])
            p.shape([(-3, -12), (-6, -17), (-10, -19.5, True), (-7.5, -14.5), (-6.5, -11.5)], pal["bone"], ink, OW, shade=pal["bone_sh"], d=(0.8, 0.8))
        elif hat == "caps_crown":
            # Hammered bottle caps on a brass band.
            band = [(-10.5, -9.5), (-3, -12.5), (6, -12), (9.5, -9.5), (9.0, -7.0), (-2.5, -9.6), (-10.2, -6.8)]
            p.shape(band, pal["gold"], ink, OW, shade=pal["gold_sh"], d=(0.8, 1.0))
            for x, y in ((-8, -11.5), (-2.5, -13.8), (3.5, -13.5), (8, -11.2)):
                p.shape([(x - 2.2, y + 1.6), (x - 1.6, y - 1.5), (x, y - 2.6, True), (x + 1.6, y - 1.5), (x + 2.2, y + 1.6)], pal["gold"], ink, OW * 0.8, shade=pal["gold_sh"], d=(0.6, 0.8), corner_n=3)
                p.ellipse((x, y - 0.4), (0.8, 0.8), H("#C0392B"))
        elif hat == "plumed_hat":
            p.shape([(-8, -9), (-6, -16), (2, -18.5), (8, -15), (9, -9)], pal["cloth"], ink, OW, shade=pal["cloth_sh"], light=pal["cloth_lt"], d=(1.4, 1.4))
            p.inner([(-7.8, -11.5), (8.8, -11.2), (8.9, -9.3), (-7.9, -9.4)], pal["gold"], corner=True)
            p.shape([(-15, -6.5), (-4, -10.5), (11, -9.5), (17, -6.0, True), (8, -7.0), (-5, -7.0), (-14, -4.5)], pal["cloth"], ink, OW, shade=pal["cloth_sh"], d=(0.6, 1.0))
            p.shape([(-4, -16), (-12, -22), (-22, -24, True), (-15, -19), (-6, -13.5)], H("#F2E7C9"), ink, OW * 0.8, shade=H("#CDBF9A"), d=(0.8, 0.8))
        elif hat == "hood_back":
            p.shape([(-15, 4), (-16, -6), (-10, -13), (-1, -15), (8, -13), (12, -8), (4, -6), (-6, -2), (-8, 8)], pal["cloth"], ink, OW, shade=pal["cloth_sh"], d=(1.6, 1.8))
        elif hat == "hood":
            p.shape([(-12.5, -3), (-10.5, -10.5), (-2, -14.5), (7, -13), (12.5, -7.5), (11, -5.5), (4, -9), (-4, -8.5), (-8, -1)], pal["cloth"], ink, OW, shade=pal["cloth_sh"], light=pal["cloth_lt"], d=(1.2, 1.4))
        elif hat == "bandana":
            p.shape([(-12.5, -5), (-9.5, -11), (-1, -13.5), (8, -11.5), (11.5, -7.5), (10.5, -5.5), (0, -7.5), (-11, -2.5)], pal["cloth"], ink, OW, shade=pal["cloth_sh"], d=(0.9, 1.1))
            p.shape([(-12, -4), (-17, -1), (-19.5, 3, True), (-15, 1), (-11.5, -1.5)], pal["cloth"], ink, OW * 0.8, shade=pal["cloth_sh"], d=(0.6, 0.8))
            for c in ((-4, -10), (3, -10.5), (7.5, -8.5)):
                p.ellipse(c, (0.7, 0.7), pal["cloth_lt"])
        elif hat == "headwrap":
            wrap = [(-12.5, -3), (-11.5, -10), (-3, -14.5), (7, -13.5), (12, -8), (11.5, -5), (2, -7), (-8, -4)]
            p.shape(wrap, pal["cloth"], ink, OW, shade=pal["cloth_sh"], light=pal["cloth_lt"], d=(1.2, 1.4))
            p.line([(-10, -6), (0, -11), (10, -8)], pal["cloth_sh"], 0.6)
            p.line([(-11, -9), (-1, -13), (8, -12)], pal["cloth_sh"], 0.6)
            p.shape([(-11, -4), (-17, 3), (-15, 8, True), (-12.5, 2), (-9, -2)], pal["cloth"], ink, OW * 0.8, shade=pal["cloth_sh"], d=(0.6, 0.8))
        elif hat == "scarf":
            p.shape([(-7, 7), (3, 9.5), (12, 8), (11, 12.5), (2, 14), (-7, 11.5)], pal["cloth"], ink, OW, shade=pal["cloth_sh"], light=pal["cloth_lt"], d=(0.8, 1.0))
            p.shape([(-6, 10), (-11, 17), (-8.5, 19, True), (-3.5, 12)], pal["cloth"], ink, OW * 0.8, shade=pal["cloth_sh"], d=(0.6, 0.8))
            for x in (-2, 3, 8):
                p.line([(x, 9.2), (x - 0.6, 13.2)], pal["cloth_lt"], 0.5)
        elif hat == "feathers":
            p.shape([(-10.5, -6), (-2, -11.8), (8, -10), (8.5, -8), (-1.5, -9.5), (-10, -4)], pal["bone"], ink, OW * 0.7, shade=pal["bone_sh"], d=(0.4, 0.6))
            for base, tip, col in (((-4, -11), (-9, -24), pal["cloth"]), ((-1, -11.6), (1, -25), pal["eye"]), ((2, -11.2), (9, -22), pal["cloth_lt"])):
                mx, my = (base[0] + tip[0]) / 2, (base[1] + tip[1]) / 2
                nx, ny = -(tip[1] - base[1]) * 0.12, (tip[0] - base[0]) * 0.12
                p.shape([base, (mx + nx, my + ny), (tip[0], tip[1], True), (mx - nx, my - ny)], col, ink, OW * 0.6, corner_n=4)
            for c in ((-6.5, -8.0), (-2.5, -10.2), (2.0, -10.0), (5.8, -9.0)):
                p.ellipse(c, (0.9, 0.9), pal["eye"], ink, 0.3)

    # -- torso ----------------------------------------------------------------------------
    def torso(self, S):
        return piece(self.key("torso"), 30, S, self._paint_torso)

    def _paint_torso(self, p: Part) -> None:
        pal, ink, L = self.pal, self.pal["ink"], self.L
        t = TORSOS[L["torso"]]
        outfit = L["outfit"]
        if "lute" in L["gear"]:
            # Slung across the back, its neck up behind the far shoulder.
            p.shape([(-6, -6), (-14, -16), (-16, -15), (-9, -3)], pal["wood_sh"], ink, OW, corner_n=2)
            p.shape([(-17, -19), (-13, -16), (-15.5, -13.5), (-19, -16)], pal["wood_sh"], ink, OW, corner_n=2)
            p.shape([(-5, -6), (0, -2), (1, 4), (-3, 9), (-9, 9), (-12, 4), (-11, -2)], pal["wood"], ink, OW, shade=pal["wood_sh"], d=(1.2, 1.4))
        p.shape(t, pal["skin"], ink, OW, shade=pal["skin_sh"], light=pal["skin_lt"], d=(2.8, 3.0))
        if outfit == "loincloth":
            p.inner([(0, -3), (8, -4), (11, 3), (7, 8), (0, 8), (-3, 3)], pal["belly"], clip=t)
            p.shape([(-11.5, 4.5), (0, 5.5), (12.5, 4.0), (12.5, 8.5), (0, 10), (-11.5, 9)], pal["cloth"], ink, OW, shade=pal["cloth_sh"], light=pal["cloth_lt"], d=(0.8, 1.2))
            p.shape([(2, 8.5), (10, 8), (11, 17.5, True), (6, 15.5), (2.5, 17, True)], pal["cloth"], ink, OW, shade=pal["cloth_sh"], d=(1.2, 1.2))
        elif outfit == "tunic":
            tun = [(-11.5, -4), (-8, -10), (-1, -12.5, True), (3, -8), (9, -9.5, True), (12.8, -2), (13, 6), (11, 14, True),
                   (8.5, 11.5, True), (5.5, 15, True), (2.5, 11.5, True), (-0.5, 14.5, True), (-3.5, 11, True), (-7, 13.5, True), (-9.5, 10, True), (-12, 5)]
            p.shape(tun, pal["cloth"], ink, OW, shade=pal["cloth_sh"], light=pal["cloth_lt"], d=(2.2, 2.4))
            p.line([(-1, -12), (3, -8), (9, -9.3)], pal["cloth_sh"], 0.8)
            p.line([(6, -3), (7.5, 4)], pal["cloth_sh"], 0.6)
            p.inner([(-12.6, 4.5), (0, 5.5), (13.2, 3.6), (13.2, 7.0), (0, 8.8), (-12.6, 8)], pal["belt"], corner=True)
            p.inner([(3.6, 4.6), (7.0, 4.4), (7.0, 8.3), (3.6, 8.5)], pal["buckle"], corner=True)
            p.inner([(4.5, 5.6), (6.1, 5.5), (6.1, 7.3), (4.5, 7.4)], pal["belt"], corner=True)
            p.shape([(-12, 7), (-7.5, 7.5), (-7.5, 12.5), (-11.5, 12.0)], pal["leather"], ink, OW * 0.8, corner_n=3)
        elif outfit == "hide":
            p.inner([(1, -4), (10, -4), (13, 4), (9, 10), (1, 9), (-2, 3)], pal["belly"], clip=t)
            p.shape([(-11.5, 5.5), (0, 6.5), (14, 5.0), (14, 9.5), (0, 11), (-11.5, 10)], pal["cloth"], ink, OW, shade=pal["cloth_sh"], light=pal["cloth_lt"], d=(0.8, 1.2))
            p.shape([(1, 9.5), (11, 9), (12.5, 16, True), (9, 14.5, True), (6.5, 17, True), (4, 14.5, True), (1.5, 16.5, True)], pal["cloth"], ink, OW, shade=pal["cloth_sh"], d=(1.0, 1.2))
            p.inner([(9.5, -9), (12, -7.5), (-9, 6.5), (-11, 4.5)], pal["belt"], clip=t, corner=True)
            p.shape([(1, -2.5), (5, -3.5), (5.5, -1.8), (1.2, -0.8)], pal["bone"], ink, OW * 0.6, corner_n=3)
        elif outfit == "kilt":
            p.inner([(2, -8), (11, -9), (15, 0), (12, 8), (3, 9), (-1, 0)], pal["belly"], clip=t)
            p.shape([(-13.5, 6), (0, 7.5), (15, 5.5), (15.2, 10.5), (0, 12.5), (-13.2, 11)], pal["cloth"], ink, OW, shade=pal["cloth_sh"], light=pal["cloth_lt"], d=(0.8, 1.2))
            p.shape([(-12, 10.5), (14.5, 9.5), (15, 18.5, True), (10, 16, True), (6, 19.5, True), (2, 16, True), (-2, 19, True), (-6.5, 15.5, True), (-11, 18, True)],
                    pal["cloth"], ink, OW, shade=pal["cloth_sh"], d=(1.4, 1.6))
            p.inner([(-13.6, 6.8), (15.2, 6.2), (15.2, 8.6), (-13.6, 9.2)], pal["leather"], corner=True)
        elif outfit == "host":
            p.inner(t, pal["shirt"], clip=t)
            p.tone(smooth(t), pal["shirt_sh"], (2.4, 2.6))
            # An open waistcoat (its back panel, and a front panel with a
            # lapel, the shirt down the chest between) over a bar apron.
            back = [(-11.6, 1), (-9.5, -7.5), (-3.5, -10.6), (2.5, -10.8, True), (0.5, -4), (1.5, 5), (0.5, 10.6, True), (-7.5, 10.2), (-11, 6)]
            front = [(8, -9), (11, -5.5), (13.2, 0), (14, 4), (13, 7.5, True), (8.5, 7.8), (6.5, 1), (5.5, -6, True)]
            p.shape(back, pal["cloth"], ink, OW * 0.8, shade=pal["cloth_sh"], d=(1.6, 1.8))
            p.shape(front, pal["cloth"], ink, OW * 0.8, shade=pal["cloth_sh"], light=pal["cloth_lt"], d=(1.0, 1.4))
            p.inner([(5.6, -6), (8.0, -8.8), (8.4, -4.5), (6.8, -1)], pal["cloth_sh"], corner=True)
            for y in (-0.5, 3.0, 6.5):
                p.ellipse((8.0 + 0.1 * y, y), (0.75, 0.75), pal["gold"], ink, 0.35)
            p.shape([(2.5, 6.5), (13.6, 6.0), (14.6, 11), (13, 21.5, True), (3.5, 22, True), (2.0, 12)], pal["apron"], ink, OW * 0.8, shade=pal["apron_sh"], d=(1.6, 1.4))
            p.inner([(-11.8, 5.8), (13.8, 5.0), (13.8, 6.9), (-11.6, 7.7)], pal["apron_sh"], corner=True)
            p.line([(8.5, 11.5), (9.0, 21)], pal["apron_sh"], 0.45)
            p.shape([(-11.5, 6.5), (-14.5, 9.5), (-13.0, 11.5), (-10.5, 8.5)], pal["apron"], ink, OW * 0.6, corner_n=2)
        elif outfit == "bard":
            p.shape([(-11.4, 0), (-9, -8), (0, -11), (9, -8.5), (12.5, -1), (14, 6), (11.5, 12), (1, 13), (-8, 11)], pal["shirt"], ink, OW * 0.8, shade=pal["shirt_sh"], d=(2.0, 2.2))
            p.line([(9, -8.5), (6, -5), (7.5, 4)], pal["shirt_sh"], 0.6)
            p.inner([(9, -9.5), (12.5, -7), (-7.5, 8.5), (-11, 6.5)], pal["cloth"], clip=t, corner=True)
            p.shape([(-12, 4), (0, 5.5), (14, 4.0), (14.2, 8.5), (0, 10.5), (-11.8, 9)], pal["cloth"], ink, OW, shade=pal["cloth_sh"], light=pal["cloth_lt"], d=(0.8, 1.2))
            p.shape([(-12.5, 7), (-9, 8), (-10, 17, True), (-13.5, 15.5, True)], pal["cloth"], ink, OW * 0.8, shade=pal["cloth_sh"], d=(0.8, 0.8))
            p.shape([(-2, 9), (13.5, 8), (13, 15, True), (-1, 15.5, True)], pal["belt"], ink, OW * 0.8, shade=pal["leather"], d=(1.0, 1.0))
        if "rope" in L["gear"]:
            for i in range(9):
                x = -13 + i * 3.4
                p.ellipse((x, 8.2 - 0.12 * x), (1.9, 1.3), pal["rope"], ink, 0.35)
        if "harness" in L["gear"]:
            p.inner([(8, -15), (11.5, -13), (-10, 7.5), (-13, 5)], pal["leather"], clip=t, corner=True)
            p.ellipse((1.5, -4.5), (1.6, 1.6), pal["iron"], ink, 0.45)

    def pauldron(self, S):
        """Iron over the near shoulder, about the shoulder joint."""
        pal, ink = self.pal, self.pal["ink"]

        def paint(p: Part):
            pa = [(-7, -2), (-1, -6.5), (6, -4.5), (8.5, 1.5, True), (4, 3.5), (-2.5, 3), (-6.5, 1)]
            p.shape(pa, pal["iron"], ink, OW, shade=pal["iron_sh"], light=pal["iron_lt"], d=(1.2, 1.4))
            p.line([(-5, -1), (0, -4.5), (6.5, -2.8)], pal["iron_sh"], 0.7)
            for c in ((-3.0, 0.0), (2.5, -1.8), (6.3, 0.8)):
                p.ellipse(c, (0.7, 0.7), pal["iron_lt"])
            for c in ((0.5, -6.6), (5.0, -5.4)):
                p.shape([(c[0] - 1.4, c[1] + 0.8), (c[0], c[1] - 2.6, True), (c[0] + 1.4, c[1] + 0.8)], pal["iron_lt"], ink, OW * 0.6, corner_n=1)

        return piece(self.key("pauldron"), 14, S, paint)

    # -- hands and feet ------------------------------------------------------------------------
    def hand(self, S, near: bool):
        pal = self.pal
        fill, sh = (pal["skin"], pal["skin_sh"]) if near else (pal["skin_far"], pal["skin_far_sh"])
        k = 1.0 + 0.45 * (self.L["limb"] - 1.0)

        def paint(p: Part):
            p.shape(scaled([(-2.4, -2.6), (2.2, -3.0), (3.9, -1.0), (4.2, 1.6), (1.8, 3.2), (-2.2, 2.6), (-3.2, 0)], k), fill, pal["ink"], OW, shade=sh, d=(0.9, 1.0))
            p.line(scaled([(0.6, -2.8), (1.6, 0.0)], k), pal["ink"], 0.45)
            p.line(scaled([(2.4, -2.4), (3.0, 0.2)], k), pal["ink"], 0.45)
            p.inner(scaled([(3.8, -1.6), (5.2, -1.0), (4.0, -0.3)], k), pal["nail"], corner=True)

        return piece(self.key("hand", near), 10, S, paint)

    def foot(self, S, near: bool):
        """A long clawed foot; its pivot is the ankle, its sole 3.6 below."""
        pal = self.pal
        fill, sh = (pal["skin"], pal["skin_sh"]) if near else (pal["skin_far"], pal["skin_far_sh"])
        k = 1.0 + 0.3 * (self.L["limb"] - 1.0)
        sole = (0.0, 3.6)

        def paint(p: Part):
            foot = scaled([(-3.5, -2.0), (1.5, -3.2), (7, -2.4), (13.5, 0.2), (16.5, 2.2, True), (12.5, 3.6), (-3.0, 3.6), (-4.6, 1.2)], k, sole)
            p.shape(foot, fill, pal["ink"], OW, shade=sh, light=pal["skin_lt"] if near else None, d=(1.1, 1.3))
            p.line(scaled([(10.0, 0.6), (11.0, 3.4)], k, sole), pal["ink"], 0.45)
            p.line(scaled([(12.8, 1.0), (13.6, 3.4)], k, sole), pal["ink"], 0.45)
            p.inner(scaled([(16.0, 1.5), (18.0, 2.9), (15.6, 3.3)], k, sole), pal["nail"], corner=True)

        return piece(self.key("foot", near), 24, S, paint)

    # -- the held item ----------------------------------------------------------------------
    def weapon(self, S, item: str):
        """The held item pointing along +x from the fist (``goblin_side.WEAPON_REACH``)."""
        return piece(self.key("weapon", item), 36, S, lambda p: self._paint_weapon(p, item))

    def _paint_weapon(self, p: Part, item: str) -> None:
        pal, ink = self.pal, self.pal["ink"]
        if item in ("sword", "dagger"):
            style = self.L.get("sword", "clean")
            p.shape([(-3.6, -1.1), (4.0, -1.1), (4.0, 1.1), (-3.6, 1.1)], pal["grip"], ink, OW * 0.8, corner_n=1)
            for x in (-2.0, 0.0, 2.0):
                p.line([(x, -1.0), (x + 0.8, 1.0)], pal["leather"] if style != "clean" else pal["metal_sh"], 0.4)
            p.ellipse((-4.3, 0), (1.3, 1.3), pal["metal_sh"], ink, OW * 0.8)
            if item == "dagger":
                blade = [(5, -1.5), (14, -1.3), (19.5, 0.2, True), (14, 1.5), (5, 1.6)]
                guard = [(3.6, -2.8), (5.4, -2.8), (5.4, 2.8), (3.6, 2.8)]
            elif style == "clean":
                blade = [(5, -1.7), (21, -1.7), (25.5, 0, True), (21, 1.7), (5, 1.7)]
                guard = [(3.6, -4.0), (5.4, -4.0), (5.4, 4.0), (3.6, 4.0)]
            elif style == "rusty":
                blade = [(5, -1.6), (12, -1.8), (12.8, -1.0, True), (13.6, -1.9, True), (19, -2.6), (25, -0.6, True), (24, 1.6), (5, 1.8)]
                guard = [(3.4, -3.4), (5.6, -3.0), (5.6, 3.4), (3.4, 3.0)]
            else:
                blade = [(5, -1.4), (9, -2.2, True), (11, -1.4, True), (14, -2.8, True), (16, -1.8, True), (20, -3.0, True), (25, 0.2, True), (18, 2.2), (5, 1.8)]
                guard = [(3.6, -2.6), (5.6, -2.6), (5.6, 2.6), (3.6, 2.6)]
            p.shape(guard, pal["leather"] if style != "clean" else pal["grip"], ink, OW * 0.8, corner_n=1)
            p.shape(blade, pal["metal"], ink, OW * 0.85, shade=pal["metal_sh"], d=(0.0, 1.2), corner_n=2)
            p.line([(6, -0.9), (blade[2][0] - 5, -0.9)], pal["metal_lt"], 0.6)
            if style == "rusty" and item == "sword":
                for c, r in (((9, 0.6), 0.9), ((17, -0.6), 0.7), ((22, 0.4), 0.6)):
                    p.ellipse(c, (r * 1.3, r), pal["rust"])
        elif item == "spear":
            p.shape([(-8, -1.0), (23, -1.0), (23, 1.0), (-8, 1.0)], pal["wood"], ink, OW * 0.8, shade=pal["wood_sh"], d=(0, 0.8), corner_n=1)
            p.line([(19.5, -1.0), (21.5, 1.0)], pal["leather"], 0.6)
            p.line([(20.5, -1.0), (22.5, 1.0)], pal["leather"], 0.6)
            p.shape([(22, -1.8), (25, -2.6), (29.5, 0, True), (25, 2.6), (22, 1.8)], pal["metal"], ink, OW * 0.8, shade=pal["metal_sh"], d=(0, 1.0), corner_n=3)
        elif item == "staff":
            p.shape([(-10, -1.1), (22, -1.3), (24, -2.4, True), (25, 1.4), (-10, 1.1)], pal["wood"], ink, OW * 0.8, shade=pal["wood_sh"], d=(0, 0.8), corner_n=2)
            p.ellipse((27.0, 0.0), (3.0, 3.0), pal["eye"], ink, OW * 0.8)
            p.ellipse((26.2, -0.9), (1.0, 1.0), pal["eye_glow"])
            for x in (-4, 6, 16):
                p.line([(x, -1.2), (x + 1.2, 1.2)], pal["wood_sh"], 0.5)
        elif item == "bow":
            # Held at the grip, limbs up and down, an arrow nocked forward.
            p.line([(-1.5, -15), (-1.5, 15)], pal["metal_lt"], 0.35)
            p.shape([(0, -1.8), (3.5, -9), (1.5, -15.5, True), (0.2, -15), (2.0, -9), (-1.0, -1.8)], pal["wood"], ink, OW * 0.7, corner_n=3)
            p.shape([(0, 1.8), (3.5, 9), (1.5, 15.5, True), (0.2, 15), (2.0, 9), (-1.0, 1.8)], pal["wood"], ink, OW * 0.7, corner_n=3)
            p.line([(-1.5, 0), (20, 0)], pal["wood_sh"], 0.8)
            p.shape([(19, -1.4), (23, 0, True), (19, 1.4)], pal["metal"], ink, OW * 0.5, corner_n=1)
            p.shape([(-2.5, -1.8), (1.5, -2.0), (1.5, 2.0), (-2.5, 1.8)], pal["leather"], ink, OW * 0.6, corner_n=1)
        else:  # hammer: a maul, a club or a tavern gavel on a haft
            kind = self.L["hammer"]
            n = {"maul": 21.0, "club": 19.0, "gavel": 19.0}[kind]
            p.shape([(-4.5, -1.5), (n, -1.7), (n, 1.7), (-4.5, 1.5)], pal["wood"], ink, OW * 0.8, shade=pal["wood_sh"], d=(0, 1.0), corner_n=1)
            for x in (-3.0, -1.0, 1.0):
                p.line([(x, -1.4), (x + 0.9, 1.4)], pal["leather"], 0.5)
            if kind == "maul":
                head = [(n - 4, -7.5), (n + 6, -7.5), (n + 6.5, -6.5, True), (n + 6.5, 7.5), (n - 4.5, 7.5), (n - 4.5, -6.5)]
                p.shape(head, pal["iron"], ink, OW, shade=pal["iron_sh"], light=pal["iron_lt"], d=(1.4, 1.6), corner_n=2)
                for y in (-4.5, 0, 4.5):
                    p.ellipse((n + 0.8, y), (0.8, 0.8), pal["iron_lt"])
                p.line([(n - 4.0, -7.2), (n - 4.0, 7.2)], pal["iron_sh"], 0.7)
            elif kind == "club":
                head = [(n - 6, -2.4), (n + 1, -5.2), (n + 6, -4.6), (n + 7.8, 0, True), (n + 6, 4.6), (n + 1, 5.2), (n - 6, 2.4)]
                p.shape(head, pal["stone"], ink, OW, shade=pal["stone_sh"], light=pal["stone_lt"], d=(1.4, 1.6))
                for c in ((n + 2, -2.4), (n + 4.5, 2.0), (n - 1.5, 1.5)):
                    p.ellipse(c, (1.0, 0.8), pal["stone_sh"])
            else:
                head = [(n - 3.5, -6.5), (n + 4.5, -6.5), (n + 5, -6), (n + 5, 6), (n + 4.5, 6.5), (n - 3.5, 6.5), (n - 4, 6), (n - 4, -6)]
                p.shape(head, pal["wood"], ink, OW, shade=pal["wood_sh"], light=pal["wood_lt"], d=(1.4, 1.4), corner_n=2)
                for y in (-4.2, 4.2):
                    p.inner([(n - 4, y - 1.0), (n + 5, y - 1.0), (n + 5, y + 1.0), (n - 4, y + 1.0)], pal["gold"], corner=True)
                    p.line([(n - 4, y + 1.0), (n + 5, y + 1.0)], pal["gold_sh"], 0.4)
