"""Opaque right-facing green goblin target for side-scrolling games.

The goblin's look is this module's drawing (an egg body and loincloth, a
rigid big-eared head with a snout and a glowing eye, stick limbs, the held
item, the archetype's accessories) and it is deliberately crude. Its MOVES
are key poses in ``_goblin_moves.py`` (a full platform-fighter moveset: a
stabbing jab string, tilts, smashes, aerials, specials, grabs and throws,
shield and dodges, the damage, ledge, item and presentation rows) and its
rows and fighter-category coverage are ``_goblin_motion.py``. A pose is laid
out here (``_layout``: the whole goblin can turn about its body, legs plant
by IK or tuck by angle, the weapon points anywhere) and drawn with the same
primitives as before. Swing smears, sparks, dust and the rest are drawn from
the pose's ``fx`` strengths, and ``attack_hitboxes`` measures each strike's
volume from where the weapon (or boot, or teeth) is on its active frames.

The ``blink_out`` and ``blink_in`` rows are Ambition's short-range teleport /
precision-blink ability split into source and destination phases, not an eyelid
blink.  The goblin remains fully opaque inside the character
silhouette; translucent pixels are reserved for outer antialiasing and FX.

For this right-facing target, the far arm is drawn behind the body and the near
weapon arm is drawn in front.  The head is drawn as a rigid local layer and then
rotated as one unit, so ears, snout, eye, mouth, and teeth do not shear apart.
"""

from __future__ import annotations

import math
import random
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageColor, ImageDraw
from ambition_sprite2d_renderer.core.draw import rgba, with_alpha, bbox_from_center as _bbox

from ...profiling import profile
from ...authoring import rigdoc, shape_rig
from ...authoring.common_draw import RESAMPLING, draw_rotated_ellipse, draw_rotated_rounded_rect
from ...authoring.generator import CharacterGenerator
from ...authoring.rig import add, clamp, ease_in_out_sine, ease_out_cubic, lerp, smoothstep, vec
from ...registry import CharacterJob
from . import _goblin_moves as MOVES
from ._goblin_motion import GOBLIN_ROWS
from ambition_sprite2d_renderer.core.draw import blending_draw

Color = Tuple[int, int, int, int]
Point = Tuple[float, float]






def parse_background(value: str) -> Optional[Color]:
    return None if str(value).lower() == "transparent" else rgba(str(value))




def _rot(p: Point, degrees: float) -> Point:
    """``p`` turned ``degrees`` clockwise on screen (y down)."""
    r = math.radians(degrees)
    return (p[0] * math.cos(r) - p[1] * math.sin(r), p[0] * math.sin(r) + p[1] * math.cos(r))


def _hull(points) -> list:
    """The convex hull of ``points`` (monotone chain)."""
    pts = sorted(set((round(x, 2), round(y, 2)) for x, y in points))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for q in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], q) <= 0:
            lower.pop()
        lower.append(q)
    for q in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], q) <= 0:
            upper.pop()
        upper.append(q)
    return lower[:-1] + upper[:-1]


def _paste_rotated_local(base: Image.Image, layer: Image.Image, center: Point, angle: float) -> None:
    """``layer`` turned ``angle`` degrees (counter-clockwise, as ``Image.rotate``)
    about its centre, placed at ``center``: one part, turned (``shape_rig``)."""
    shape_rig.place(base, (layer, (layer.width / 2, layer.height / 2)), center, -angle, "head")


@dataclass(frozen=True)
class GoblinSpec:
    target: str
    seed: int
    archetype: str
    held_item: str
    palette_name: str
    head_w: float
    head_h: float
    snout_len: float
    ear_w: float
    ear_h: float
    body_w: float
    body_h: float
    arm_upper: float
    arm_lower: float
    leg_upper: float
    leg_lower: float
    hand_r: float
    foot_w: float
    foot_h: float
    eye_w: float
    eye_h: float
    tooth_size: float


@dataclass
class GoblinPose:
    """One frame of the goblin, as ``_goblin_moves`` keys it (see that
    module's docstring for each field). Angles are clockwise on screen."""

    x: float = 0.0
    y: float = 0.0
    spin: float = 0.0
    bx: float = 0.0
    by: float = 0.0
    tilt: float = 0.0
    hx: float = 0.0
    hy: float = 0.0
    head: float = 0.0
    nu: float = 28.0
    nl: float = 18.0
    fu: float = 136.0
    fl: float = 152.0
    wa: float = -18.0
    wpn: float = 1.0
    nleg: tuple = ("a", 62.0, 82.0)
    fleg: tuple = ("a", 92.0, 98.0)
    blink: bool = False
    squint: float = 0.0
    dead: bool = False
    mouth: float = 0.0
    #: The far arm drawn in front of the body (a grab, a held item, a punch).
    fz: float = 0.0
    fx: Dict[str, float] = field(default_factory=dict)

    @classmethod
    def from_moves(cls, values: Dict[str, object]) -> "GoblinPose":
        fx = {k[3:]: float(v) for k, v in values.items() if k.startswith("fx.")}
        fields_ = {k: v for k, v in values.items() if not k.startswith("fx.") and k in cls.__dataclass_fields__}
        return cls(fx=fx, **fields_)


class SideGoblinGenerator(CharacterGenerator):
    #: Every frame is painted through rigdoc's seams: the sheet publishes its
    #: part flipbook (``authoring.sheet.publish_generator_flipbook``).
    publishes_part_flipbook = True

    name = "goblin"
    target = "goblin"

    #: Every row the goblin can publish (``_goblin_motion.GOBLIN_ROWS``); a
    #: config's ``animations`` list picks which ones its sheet carries. The
    #: rows ``blink_out`` / ``blink_in`` are Ambition's teleport (see the
    #: module docstring).
    ANIMATIONS: Dict[str, Dict[str, int]] = {
        name: {"frames": frames, "duration_ms": ms} for name, frames, ms in GOBLIN_ROWS
    }

    PALETTES = {
        "classic": {
            "skin": rgba("#67A84B"),
            "skin_top": rgba("#96D46B"),
            "skin_shadow": rgba("#3D6C2B"),
            "belly": rgba("#83BD5D"),
            "cloth": rgba("#6D2BA0"),
            "cloth_dark": rgba("#4B1E72"),
            "eye": rgba("#F24DFF"),
            "eye_glow": rgba("#FFD0FF"),
            "outline": rgba("#15171B"),
            "mouth": rgba("#2A1B18"),
            "tooth": rgba("#F4EBD5"),
            "weapon": rgba("#A963F8"),
            "weapon_dark": rgba("#6A2CC1"),
            "metal": rgba("#E2E4EA"),
            "shadow": rgba("#000000", 34),
        },
        "forest": {
            "skin": rgba("#5C9248"),
            "skin_top": rgba("#8CC66B"),
            "skin_shadow": rgba("#345B2A"),
            "belly": rgba("#74AA58"),
            "cloth": rgba("#6D2BA0"),
            "cloth_dark": rgba("#4B1E72"),
            "eye": rgba("#EF52FF"),
            "eye_glow": rgba("#F6BCFF"),
            "outline": rgba("#15171B"),
            "mouth": rgba("#261D22"),
            "tooth": rgba("#F4EBD5"),
            "weapon": rgba("#B169FF"),
            "weapon_dark": rgba("#6A2CC1"),
            "metal": rgba("#DADCE4"),
            "shadow": rgba("#000000", 34),
        },
        "cave": {
            "skin": rgba("#5F6F68"), "skin_top": rgba("#8EA29A"), "skin_shadow": rgba("#35423E"), "belly": rgba("#778A82"),
            "cloth": rgba("#394BA0"), "cloth_dark": rgba("#242C69"), "eye": rgba("#6BE9FF"), "eye_glow": rgba("#D9FFFF"),
            "outline": rgba("#15171B"), "mouth": rgba("#251D1D"), "tooth": rgba("#F4EBD5"), "weapon": rgba("#75B8FF"),
            "weapon_dark": rgba("#2D5E98"), "metal": rgba("#CDD3DA"), "shadow": rgba("#000000", 36),
        },
        "desert": {
            "skin": rgba("#A7A34B"), "skin_top": rgba("#D4C76B"), "skin_shadow": rgba("#67632B"), "belly": rgba("#BDB65D"),
            "cloth": rgba("#B06B2A"), "cloth_dark": rgba("#72451D"), "eye": rgba("#FF7059"), "eye_glow": rgba("#FFD0C7"),
            "outline": rgba("#15171B"), "mouth": rgba("#2A1B18"), "tooth": rgba("#F4EBD5"), "weapon": rgba("#FFB15E"),
            "weapon_dark": rgba("#9A5A25"), "metal": rgba("#E7DDC4"), "shadow": rgba("#000000", 34),
        },
        "frost": {
            "skin": rgba("#6EA0A3"), "skin_top": rgba("#A8DDE0"), "skin_shadow": rgba("#3B686B"), "belly": rgba("#85BFC0"),
            "cloth": rgba("#5063B8"), "cloth_dark": rgba("#2B3677"), "eye": rgba("#FFFFFF"), "eye_glow": rgba("#B6FFF5"),
            "outline": rgba("#15171B"), "mouth": rgba("#1E2527"), "tooth": rgba("#F4EBD5"), "weapon": rgba("#9FEAFF"),
            "weapon_dark": rgba("#37798C"), "metal": rgba("#E2F6FA"), "shadow": rgba("#000000", 34),
        },
        "brute": {
            "skin": rgba("#7B8F35"), "skin_top": rgba("#A8C24D"), "skin_shadow": rgba("#4D5C23"), "belly": rgba("#8DA544"),
            "cloth": rgba("#8A3A2B"), "cloth_dark": rgba("#5C241B"), "eye": rgba("#FF7059"), "eye_glow": rgba("#FFD0C7"),
            "outline": rgba("#15171B"), "mouth": rgba("#2A1B18"), "tooth": rgba("#F4EBD5"), "weapon": rgba("#FF8A5E"),
            "weapon_dark": rgba("#A0432D"), "metal": rgba("#E2D3C0"), "shadow": rgba("#000000", 38),
        },
        "shaman": {
            "skin": rgba("#4C8A5B"), "skin_top": rgba("#78C987"), "skin_shadow": rgba("#2E5D37"), "belly": rgba("#6BAB73"),
            "cloth": rgba("#7E4FCC"), "cloth_dark": rgba("#4C2C87"), "eye": rgba("#FFE36E"), "eye_glow": rgba("#FFF6B0"),
            "outline": rgba("#15171B"), "mouth": rgba("#261D22"), "tooth": rgba("#F4EBD5"), "weapon": rgba("#B98CFF"),
            "weapon_dark": rgba("#6A2CC1"), "metal": rgba("#DADCE4"), "shadow": rgba("#000000", 34),
        },
        "chieftain": {
            "skin": rgba("#6E9238"), "skin_top": rgba("#B4CF55"), "skin_shadow": rgba("#3F5C25"), "belly": rgba("#93AA47"),
            "cloth": rgba("#C07039"), "cloth_dark": rgba("#6B2F1F"), "eye": rgba("#FFDA66"), "eye_glow": rgba("#FFF0A8"),
            "outline": rgba("#15171B"), "mouth": rgba("#291815"), "tooth": rgba("#F4EBD5"), "weapon": rgba("#FFB15E"),
            "weapon_dark": rgba("#934A25"), "metal": rgba("#E7D2A8"), "shadow": rgba("#000000", 38),
        },
        "bard": {
            "skin": rgba("#5B9A56"), "skin_top": rgba("#8FD36F"), "skin_shadow": rgba("#376333"), "belly": rgba("#78B763"),
            "cloth": rgba("#D85EA5"), "cloth_dark": rgba("#842E69"), "eye": rgba("#FFE36E"), "eye_glow": rgba("#FFF6B0"),
            "outline": rgba("#15171B"), "mouth": rgba("#261D22"), "tooth": rgba("#F4EBD5"), "weapon": rgba("#FFD65A"),
            "weapon_dark": rgba("#A96B22"), "metal": rgba("#DADCE4"), "shadow": rgba("#000000", 34),
        },
    }

    def build_spec(self, job: CharacterJob) -> GoblinSpec:
        seed, archetype, held_item = job.seed, job.archetype, job.held_item
        rng = random.Random(seed)
        archetype_key = str(archetype or "default").lower()
        palette_name = "classic"
        for token, palette in [
            ("chieftain", "chieftain"),
            ("chief", "chieftain"),
            ("bard", "bard"),
            ("drummer", "bard"),
            ("brute", "brute"),
            ("shaman", "shaman"),
            ("cave", "cave"),
            ("desert", "desert"),
            ("frost", "frost"),
            ("scout", "forest"),
            ("forest", "forest"),
        ]:
            if token in archetype_key:
                palette_name = palette
                break
        if archetype != "default" and palette_name == "classic":
            palette_name = "forest"
        if held_item is None:
            if any(token in archetype_key for token in ["chieftain", "chief", "brute"]):
                held_item = "hammer"
            elif any(token in archetype_key for token in ["shaman", "bard", "drummer"]):
                held_item = "staff"
            elif "scout" in archetype_key:
                held_item = "bow"
            else:
                held_item = rng.choice(["dagger", "spear", "sword"])
        scale = 1.0
        if any(token in archetype_key for token in ["chieftain", "chief", "brute"]):
            scale = 1.14
        elif "scout" in archetype_key:
            scale = 0.93
        elif any(token in archetype_key for token in ["shaman", "bard", "drummer"]):
            scale = 1.02
        return GoblinSpec(
            target=self.name,
            seed=seed,
            archetype=archetype,
            held_item=held_item,
            palette_name=palette_name,
            head_w=rng.uniform(29.0, 32.0) * scale,
            head_h=rng.uniform(23.5, 26.0) * scale,
            snout_len=rng.uniform(7.0, 8.5) * scale,
            ear_w=rng.uniform(15.0, 17.0) * scale,
            ear_h=rng.uniform(11.0, 13.0) * scale,
            body_w=rng.uniform(21.0, 23.0) * scale,
            body_h=rng.uniform(18.0, 20.0) * scale,
            arm_upper=rng.uniform(11.5, 13.0) * scale,
            arm_lower=rng.uniform(10.5, 12.0) * scale,
            leg_upper=rng.uniform(11.0, 13.0) * scale,
            leg_lower=rng.uniform(10.5, 12.0) * scale,
            hand_r=rng.uniform(3.2, 3.8) * scale,
            foot_w=rng.uniform(10.5, 12.0) * scale,
            foot_h=rng.uniform(4.8, 5.6) * scale,
            eye_w=rng.uniform(4.5, 5.4) * scale,
            eye_h=rng.uniform(7.2, 8.8) * scale,
            tooth_size=rng.uniform(2.4, 3.2) * scale,
        )

    def sample_spec(self, job: CharacterJob) -> GoblinSpec:
        # Remembered so ``attack_hitboxes`` (which the sheet asks for by frame
        # size alone) measures this goblin's own limbs and weapon.
        spec = super().sample_spec(job)
        self._last_spec = spec
        return spec

    def pose_for_animation(self, animation: str, frame_index: int, frame_count: int) -> GoblinPose:
        return self.pose_at(animation, MOVES.clip_time(animation, frame_index, frame_count))

    def pose_at(self, animation: str, t: float) -> GoblinPose:
        """The goblin's pose at clip time ``t`` (``_goblin_moves``)."""
        return GoblinPose.from_moves(MOVES.pose(animation, t))

    def _draw_body(self, img: Image.Image, center: Point, spec: GoblinSpec, pal: Dict[str, Color], S: float, angle: float,
                   spin: float = 0.0) -> None:
        """The body egg (``angle`` counter-clockwise, as before) with its belly
        and loincloth, the whole turned clockwise by ``spin``."""
        outline = pal["outline"]
        draw_rotated_ellipse(img, center, (spec.body_w * S, spec.body_h * S), angle, pal["skin"], outline, 1.7 * S)
        bx, by = _rot((2 * S, 2 * S), spin)
        draw_rotated_ellipse(img, (center[0] + bx, center[1] + by), (spec.body_w * 0.58 * S, spec.body_h * 0.60 * S), angle, pal["belly"], None, 0)
        # Opaque cloth silhouette over body: one piece riding the body centre.
        local = 20 * S

        def paint(d) -> None:
            x, y = local, local
            cloth = [(x - 8 * S, y + 7 * S), (x + 8 * S, y + 7 * S), (x + 11 * S, y + 15 * S), (x - 6 * S, y + 13 * S)]
            d.polygon(cloth, fill=pal["cloth"], outline=outline)
            d.line([cloth[0], cloth[2]], fill=pal["cloth_dark"], width=max(1, int(1.2 * S)))

        part = shape_rig.piece(("goblin_cloth", pal["cloth"], pal["cloth_dark"], outline, S), (2 * local, 2 * local), (local, local), paint)
        shape_rig.place(img, part, center, spin, "cloth")

    def _draw_rigid_head(self, img: Image.Image, center: Point, spec: GoblinSpec, pal: Dict[str, Color], S: float, angle: float, blink: bool, squint: float, dead: bool, mouth: float = 0.0) -> Point:
        pad = int(math.ceil(54 * S))
        squint = round(squint * 10.0) / 10.0
        # Three jaw states (shut, open, gaping) keep the head pieces few.
        mouth = round(min(1.0, max(0.0, mouth)) * 2.0) / 2.0
        key = ("goblin_head", spec, spec.palette_name, S, blink, squint, dead, mouth)
        layer, _pivot = shape_rig.piece(key, (pad * 2, pad * 2), (pad, pad), lambda d: self._paint_head(d, pad, spec, pal, S, blink, squint, dead, mouth))
        _paste_rotated_local(img, layer, center, angle)
        return (center[0] + spec.head_w * 0.42 * S + 6 * S, center[1] + 0.5 * S)

    def _paint_head(self, d, pad: int, spec: GoblinSpec, pal: Dict[str, Color], S: float, blink: bool, squint: float, dead: bool, mouth: float = 0.0) -> None:
        """The head in its own frame, centred on ``(pad, pad)``."""
        layer = d._img
        cx, cy = float(pad), float(pad)
        outline = pal["outline"]
        ow = 1.8 * S
        # Ears point backward (left), while snout/eye face right.
        far_ear = [(cx - 9 * S, cy - 5 * S), (cx - 29 * S, cy - 10 * S), (cx - 12 * S, cy + 4 * S)]
        near_ear = [(cx - 3 * S, cy - 7 * S), (cx - 31 * S, cy - 13 * S), (cx - 10 * S, cy + 5 * S)]
        d.polygon(far_ear, fill=pal["skin_shadow"], outline=outline)
        # Head ellipse with opaque fill.
        head_outer = _bbox((cx, cy), spec.head_w * S + 2 * ow, spec.head_h * S + 2 * ow)
        head_inner = _bbox((cx, cy), spec.head_w * S, spec.head_h * S)
        d.ellipse(head_outer, fill=outline)
        d.ellipse(head_inner, fill=pal["skin"])
        d.polygon(near_ear, fill=pal["skin"], outline=outline)
        d.polygon([(cx - 15 * S, cy - 9 * S), (cx - 25 * S, cy - 10 * S), (cx - 13 * S, cy + 1 * S)], fill=pal["cloth"])
        # Snout.
        snout_center = (cx + spec.head_w * 0.42 * S, cy + 2.5 * S)
        snout_outer = _bbox(snout_center, spec.snout_len * 1.65 * S + ow, spec.head_h * 0.38 * S + ow)
        snout_inner = _bbox(snout_center, spec.snout_len * 1.65 * S, spec.head_h * 0.38 * S)
        d.ellipse(snout_outer, fill=outline)
        d.ellipse(snout_inner, fill=pal["skin_shadow"])
        # Semi-transparent highlight composited over opaque base, preserving alpha.
        detail = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        hd = blending_draw(detail)
        hd.ellipse((cx - 8 * S, cy - 10 * S, cx + 12 * S, cy + 1 * S), fill=with_alpha(pal["skin_top"], 125))
        rigdoc.composite_canvas(layer, detail)
        # Eye.
        eye_center = (cx + 7.5 * S, cy - 2.0 * S)
        eye_h = spec.eye_h * S * (0.20 if blink else max(0.30, 1.0 - 0.5 * squint))
        if dead:
            r = 3.0 * S
            d.line([(eye_center[0] - r, eye_center[1] - r), (eye_center[0] + r, eye_center[1] + r)], fill=pal["eye"], width=max(1, int(1.2 * S)))
            d.line([(eye_center[0] - r, eye_center[1] + r), (eye_center[0] + r, eye_center[1] - r)], fill=pal["eye"], width=max(1, int(1.2 * S)))
        elif blink:
            d.line([(eye_center[0] - 3 * S, eye_center[1]), (eye_center[0] + 3 * S, eye_center[1])], fill=pal["eye"], width=max(1, int(1.2 * S)))
        else:
            d.ellipse((eye_center[0] - spec.eye_w * S / 2, eye_center[1] - eye_h / 2, eye_center[0] + spec.eye_w * S / 2, eye_center[1] + eye_h / 2), fill=pal["eye"])
            d.ellipse((eye_center[0] - 0.8 * S, eye_center[1] - 2.5 * S, eye_center[0] + 0.6 * S, eye_center[1] - 1.1 * S), fill=pal["eye_glow"])
        # Mouth and teeth.
        mouth_a = (snout_center[0] - 3 * S, snout_center[1] + 3 * S)
        mouth_b = (snout_center[0] + 5 * S, snout_center[1] + 3.5 * S)
        if mouth > 0.0:
            # The jaw dropped: a crude dark wedge, the fang still hanging from
            # the top lip and a stub of a tooth coming up from the bottom.
            drop = (3.0 + 4.0 * mouth) * S
            jaw = [(mouth_a[0] - 1 * S, mouth_a[1] - 0.5 * S), (mouth_b[0] + 1 * S, mouth_b[1] - 1 * S),
                   (mouth_b[0] - 1 * S, mouth_b[1] + drop), (mouth_a[0] + 1 * S, mouth_a[1] + drop * 0.8)]
            d.polygon(jaw, fill=pal["mouth"], outline=outline)
            bottom = (mouth_b[0] - 3 * S, mouth_b[1] + drop * 0.9)
            d.polygon([(bottom[0] - 0.9 * S, bottom[1]), (bottom[0] + 0.9 * S, bottom[1]), (bottom[0], bottom[1] - spec.tooth_size * 0.8 * S)], fill=pal["tooth"], outline=outline)
        else:
            d.line([mouth_a, mouth_b], fill=pal["mouth"], width=max(1, int(1.1 * S)))
        d.polygon([(mouth_a[0] + 1 * S, mouth_a[1]), (mouth_a[0] + 2.7 * S, mouth_a[1]), (mouth_a[0] + 1.9 * S, mouth_a[1] + spec.tooth_size * S)], fill=pal["tooth"], outline=outline)


    def _limb_chain(self, root: Point, upper: float, lower: float, a1: float, a2: float) -> Tuple[Point, Point]:
        mid = add(root, vec(upper, a1))
        end = add(mid, vec(lower, a2))
        return mid, end

    def _solve_leg_ik(self, hip: Point, ankle: Point, upper_len: float, lower_len: float, bend_sign: float = 1.0) -> Tuple[Point, float, float]:
        """Solve a two-segment side-view leg toward a reachable ankle target.

        This is the same baseline used by the compact player walk: fixed upper
        and lower segment lengths, authored ankle targets, and forward-bending
        knees for a right-facing side profile.
        """
        dx = ankle[0] - hip[0]
        dy = ankle[1] - hip[1]
        dist = math.hypot(dx, dy)
        min_reach = abs(upper_len - lower_len) + 0.001
        max_reach = max(min_reach + 0.001, upper_len + lower_len - 0.001)
        dist = clamp(dist, min_reach, max_reach)
        base = math.degrees(math.atan2(dy, dx))
        cos_off = clamp((upper_len * upper_len + dist * dist - lower_len * lower_len) / (2.0 * upper_len * dist), -1.0, 1.0)
        off = math.degrees(math.acos(cos_off))
        a1 = base - bend_sign * off
        knee = add(hip, vec(upper_len, a1))
        a2 = math.degrees(math.atan2(ankle[1] - knee[1], ankle[0] - knee[0]))
        return knee, a1, a2

    def _draw_weapon(self, d: ImageDraw.ImageDraw, hand: Point, spec: GoblinSpec, pal: Dict[str, Color], S: float, slash_arc: float) -> None:
        angle = -18 + slash_arc * 36
        handle = add(hand, vec(7 * S, angle))
        d.line([hand, handle], fill=pal["outline"], width=max(1, int(2.0 * S)))
        d.line([hand, handle], fill=pal["weapon_dark"], width=max(1, int(1.0 * S)))
        item = spec.held_item.lower()
        if item == "spear":
            tip = add(handle, vec(20 * S, angle + 2))
            d.line([handle, tip], fill=pal["outline"], width=max(1, int(1.8 * S)))
            d.line([handle, tip], fill=pal["weapon"], width=max(1, int(0.9 * S)))
            d.polygon([tip, add(tip, (-5 * S, -3 * S)), add(tip, (-4 * S, 3 * S))], fill=pal["metal"], outline=pal["outline"])
        elif item == "sword":
            tip = add(handle, vec(18 * S, angle - 6))
            d.line([handle, tip], fill=pal["outline"], width=max(1, int(4.0 * S)))
            d.line([handle, tip], fill=pal["metal"], width=max(1, int(2.0 * S)))
        elif item == "hammer":
            tip = add(handle, vec(16 * S, angle - 4))
            d.line([handle, tip], fill=pal["outline"], width=max(1, int(4.0 * S)))
            d.line([handle, tip], fill=pal["weapon_dark"], width=max(1, int(2.0 * S)))
            head = add(tip, vec(4 * S, angle - 5))
            d.rounded_rectangle((head[0] - 5*S, head[1] - 5*S, head[0] + 8*S, head[1] + 5*S), radius=2*S, fill=pal["metal"], outline=pal["outline"], width=max(1, int(1.0*S)))
        elif item == "staff":
            tip = add(handle, vec(22 * S, angle + 1))
            d.line([handle, tip], fill=pal["outline"], width=max(1, int(3.0 * S)))
            d.line([handle, tip], fill=pal["weapon_dark"], width=max(1, int(1.4 * S)))
            d.ellipse((tip[0] - 5*S, tip[1] - 5*S, tip[0] + 5*S, tip[1] + 5*S), fill=pal["eye"], outline=pal["outline"], width=max(1, int(0.9*S)))
        elif item == "bow":
            tip = add(handle, vec(16 * S, angle - 4))
            d.arc((tip[0] - 4*S, tip[1] - 17*S, tip[0] + 14*S, tip[1] + 17*S), start=250, end=105, fill=pal["weapon"], width=max(1, int(2.0*S)))
            d.line([(tip[0] + 6*S, tip[1] - 12*S), (tip[0] + 6*S, tip[1] + 12*S)], fill=pal["metal"], width=max(1, int(0.8*S)))
            d.line([handle, (tip[0] + 19*S, tip[1])], fill=pal["metal"], width=max(1, int(1.1*S)))
        else:
            tip = add(handle, vec(12 * S, angle - 10))
            d.line([handle, tip], fill=pal["outline"], width=max(1, int(3.4 * S)))
            d.line([handle, tip], fill=pal["metal"], width=max(1, int(1.7 * S)))

    def _place_weapon(self, img: Image.Image, hand: Point, spec: GoblinSpec, pal: Dict[str, Color], S: float, angle: float) -> None:
        """The held item as one piece: painted once pointing straight ahead
        and turned about the hand to ``angle`` (clockwise, the pose's ``wa``)."""
        reach = 48 * S
        part = shape_rig.piece(
            ("goblin_weapon", spec.held_item.lower(), spec.palette_name, S),
            (2 * reach, 2 * reach),
            (reach, reach),
            lambda d: self._draw_weapon(d, (reach, reach), spec, pal, S, 0.5),
        )
        shape_rig.place(img, part, hand, angle, "weapon")

    def _place_variant_accessories(self, img: Image.Image, spec: GoblinSpec, pal: Dict[str, Color], S: float, body_center: Point, head_center: Point, body_angle: float = 0.0, head_angle: float = 0.0) -> None:
        """The archetype's accessories as two pieces, one riding the head and
        one the body: each is the accessory painter with the other anchor far
        off its canvas, so only its own items land."""
        span = 60 * S
        away = (-100 * span, -100 * span)
        for which, at in (("head", head_center), ("body", body_center)):
            local = (span, span)
            part = shape_rig.piece(
                ("goblin_accessories", which, spec.archetype, spec.palette_name, S),
                (2 * span, 2 * span),
                local,
                lambda d, which=which, local=local: self._draw_variant_accessories(
                    d, spec, pal, S, 0.0, 0.0, local if which == "body" else away, local if which == "head" else away
                ),
            )
            shape_rig.place(img, part, at, head_angle if which == "head" else body_angle, f"{which}_accessories")

    def _draw_blink_out_fx(self, img: Image.Image, root_x: float, ground_y: float, S: float, frame_index: int, frame_count: int, pal: Dict[str, Color]) -> None:
        d = blending_draw(img)
        t = 0.0 if frame_count <= 1 else frame_index / float(frame_count - 1)
        charge = smoothstep(clamp(t / 0.56, 0.0, 1.0))
        burst = smoothstep(clamp((t - 0.32) / 0.48, 0.0, 1.0))
        source_x = root_x + 9 * S
        mid_y = ground_y - 48 * S

        for rscale, alpha in [
            (0.62 + 0.55 * charge, int(145 * max(charge, 0.15))),
            (0.44 + 0.70 * burst, int(110 * max(burst, 0.12))),
        ]:
            rx, ry = 8.0 * S * rscale, 13.0 * S * rscale
            box = (source_x - rx, mid_y - ry - 4 * S, source_x + rx, mid_y + ry - 4 * S)
            d.ellipse(box, outline=with_alpha(pal["eye"], alpha), width=max(1, int(1.3 * S)))

        for i, dx in enumerate((-10, -4, 3, 10)):
            height = (27.0 - i * 2.2 + 8.0 * burst) * S
            alpha = int((88 - i * 14) * max(charge, burst))
            if alpha > 0:
                x = source_x + dx * S
                d.line([(x, mid_y - height / 2), (x + 6 * S, mid_y + height / 2)], fill=with_alpha(pal["cloth"], alpha), width=max(1, int(1.6 * S)))
                d.line([(x + 3 * S, mid_y - height / 2), (x - 4 * S, mid_y + height / 2)], fill=with_alpha(pal["eye"], max(18, alpha - 20)), width=max(1, int(0.9 * S)))

        for i in range(4):
            frac = i / 3.0 if 3 else 0.0
            sx = source_x - 9 * S + frac * 18 * S
            sy = mid_y - 11 * S - frac * 6 * S
            ex = sx + (6 + i * 2) * S
            ey = sy - (8 + i * 2) * S
            d.line([(sx, sy), (ex, ey)], fill=with_alpha(pal["eye"], int(62 * max(charge, burst))), width=max(1, int(1.0 * S)))

        ripple_alpha = int(76 * max(charge, burst))
        if ripple_alpha > 0:
            d.ellipse((source_x - 18 * S, ground_y - 7 * S, source_x + 15 * S, ground_y + 1 * S), outline=with_alpha(pal["cloth"], ripple_alpha), width=max(1, int(1.0 * S)))

    def _draw_blink_in_fx(self, img: Image.Image, root_x: float, ground_y: float, S: float, frame_index: int, frame_count: int, pal: Dict[str, Color]) -> None:
        d = blending_draw(img)
        t = 0.0 if frame_count <= 1 else frame_index / float(frame_count - 1)
        appear = smoothstep(clamp(t / 0.60, 0.0, 1.0))
        settle = ease_out_cubic(appear)
        dest_x = root_x + 9 * S
        mid_y = ground_y - 48 * S

        for rscale, alpha in [
            (1.25 - 0.45 * settle, int(150 * max(0.18, 1.0 - t * 0.55))),
            (0.52 + 0.30 * appear, int(116 * max(0.20, 1.0 - t * 0.35))),
        ]:
            rx, ry = 8.2 * S * rscale, 13.0 * S * rscale
            box = (dest_x - rx, mid_y - ry - 4 * S, dest_x + rx, mid_y + ry - 4 * S)
            d.ellipse(box, outline=with_alpha(pal["eye"], alpha), width=max(1, int(1.3 * S)))

        for i, dx in enumerate((-14, -7, 0, 8, 14)):
            height = (28.0 - i * 2.5 + 7.0 * (1.0 - settle)) * S
            alpha = int((92 - i * 12) * max(0.18, 1.0 - t * 0.42))
            x = dest_x + dx * S
            d.line([(x, mid_y - height / 2), (dest_x, mid_y)], fill=with_alpha(pal["cloth"], alpha), width=max(1, int(1.5 * S)))
            d.line([(x, mid_y + height / 2), (dest_x + 2 * S, mid_y - 2 * S)], fill=with_alpha(pal["eye"], max(16, alpha - 18)), width=max(1, int(0.9 * S)))

        ripple_alpha = int(76 * max(0.18, 1.0 - t * 0.35))
        d.ellipse((dest_x - 18 * S, ground_y - 7 * S, dest_x + 15 * S, ground_y + 1 * S), outline=with_alpha(pal["eye"], ripple_alpha), width=max(1, int(1.0 * S)))

    def _composite_teleport_actor(self, base: Image.Image, actor: Image.Image, animation: str, frame_index: int, frame_count: int, S: float) -> None:
        alpha_bbox = actor.getchannel("A").getbbox()
        if alpha_bbox is None:
            return
        x1, y1, x2, y2 = alpha_bbox
        t = 0.0 if frame_count <= 1 else frame_index / float(frame_count - 1)
        slice_w = max(1, int(5 * S))
        if animation == "blink_out":
            progress = smoothstep(clamp((t - 0.02) / 0.98, 0.0, 1.0))
            for i, x in enumerate(range(x1, x2, slice_w)):
                strip = actor.crop((x, y1, min(x + slice_w, x2), y2))
                if strip.getchannel("A").getbbox() is None:
                    continue
                frac = 0.5 if x2 == x1 else ((x + slice_w * 0.5) - x1) / float(max(1, x2 - x1))
                dx = (frac - 0.5) * (21.0 * S * progress) + math.sin(frac * math.pi * 7.0 + progress * 6.0) * 1.6 * S * progress
                dy = -(5.0 + abs(frac - 0.5) * 17.0) * S * progress
                alpha_scale = max(0.06, 1.0 - 0.88 * progress)
                if progress > 0.35 and (i + int(progress * 9)) % 3 == 0:
                    alpha_scale *= 0.35
                a = strip.getchannel("A").point(lambda v, s=alpha_scale: max(0, min(255, int(v * s))))
                strip.putalpha(a)
                rigdoc.composite_layer(base, strip, (int(x + dx), int(y1 + dy)), name="strip")
        else:
            progress = smoothstep(clamp(t / 1.0, 0.0, 1.0))
            for i, x in enumerate(range(x1, x2, slice_w)):
                strip = actor.crop((x, y1, min(x + slice_w, x2), y2))
                if strip.getchannel("A").getbbox() is None:
                    continue
                frac = 0.5 if x2 == x1 else ((x + slice_w * 0.5) - x1) / float(max(1, x2 - x1))
                dx = (frac - 0.5) * (22.0 * S * (1.0 - progress))
                dy = -(3.0 + abs(frac - 0.5) * 15.0) * S * (1.0 - progress)
                alpha_scale = min(1.0, 0.18 + 0.94 * progress)
                if progress < 0.45 and (i + frame_index) % 4 == 0:
                    alpha_scale *= 0.55
                a = strip.getchannel("A").point(lambda v, s=alpha_scale: max(0, min(255, int(v * s))))
                strip.putalpha(a)
                rigdoc.composite_layer(base, strip, (int(x + dx), int(y1 + dy)), name="strip")
            full_alpha = smoothstep(clamp((progress - 0.34) / 0.66, 0.0, 1.0))
            if full_alpha > 0:
                # Faded as one picture (one overlay), not part by part.
                rigdoc.composite_layer(base, rigdoc.faded_canvas(actor, full_alpha), name="resolved")


    def _draw_variant_accessories(self, d: ImageDraw.ImageDraw, spec: GoblinSpec, pal: Dict[str, Color], S: float, root_x: float, ground_y: float, body_center: Point, head_center: Point) -> None:
        name = (spec.archetype or "").lower()
        outline = pal["outline"]
        if any(token in name for token in ["chieftain", "chief"]):
            # Crude crown, boss pauldrons, and rally banner silhouette.
            for dx in (-12, 0, 12):
                d.polygon([(head_center[0] + dx*S - 7*S, head_center[1] - 27*S), (head_center[0] + dx*S, head_center[1] - 42*S), (head_center[0] + dx*S + 7*S, head_center[1] - 27*S)], fill=pal["weapon"], outline=outline)
            d.rounded_rectangle((body_center[0] - 22*S, body_center[1] - 14*S, body_center[0] - 5*S, body_center[1] - 3*S), radius=4*S, fill=pal["metal"], outline=outline, width=max(1, int(1*S)))
            d.rounded_rectangle((body_center[0] + 8*S, body_center[1] - 14*S, body_center[0] + 25*S, body_center[1] - 3*S), radius=4*S, fill=pal["metal"], outline=outline, width=max(1, int(1*S)))
            d.line([(body_center[0] - 24*S, body_center[1] + 15*S), (body_center[0] - 24*S, body_center[1] - 26*S)], fill=outline, width=max(1, int(2*S)))
            d.polygon([(body_center[0] - 24*S, body_center[1] - 26*S), (body_center[0] - 5*S, body_center[1] - 19*S), (body_center[0] - 24*S, body_center[1] - 12*S)], fill=pal["cloth"], outline=outline)
        elif any(token in name for token in ["bard", "drummer"]):
            # Ear tassels and little drum/sound charm for the music faction tie-in.
            d.arc((head_center[0] - 24*S, head_center[1] - 34*S, head_center[0] + 24*S, head_center[1] - 8*S), start=205, end=335, fill=pal["weapon"], width=max(1, int(1.8*S)))
            for dx in (-22, 24):
                d.line([(head_center[0] + dx*S, head_center[1] - 13*S), (head_center[0] + dx*S, head_center[1] + 5*S)], fill=pal["cloth"], width=max(1, int(2*S)))
                d.ellipse((head_center[0] + dx*S - 3*S, head_center[1] + 4*S, head_center[0] + dx*S + 3*S, head_center[1] + 10*S), fill=pal["weapon"], outline=outline)
            d.ellipse((body_center[0] - 24*S, body_center[1] + 2*S, body_center[0] - 6*S, body_center[1] + 20*S), fill=pal["cloth_dark"], outline=outline, width=max(1, int(1*S)))
            d.line([(body_center[0] - 22*S, body_center[1] + 10*S), (body_center[0] - 8*S, body_center[1] + 9*S)], fill=pal["weapon"], width=max(1, int(1*S)))
        elif "brute" in name:
            d.rounded_rectangle((body_center[0] - 19*S, body_center[1] - 13*S, body_center[0] - 4*S, body_center[1] - 3*S), radius=4*S, fill=pal["metal"], outline=outline, width=max(1, int(1*S)))
            d.rounded_rectangle((body_center[0] + 7*S, body_center[1] - 13*S, body_center[0] + 23*S, body_center[1] - 3*S), radius=4*S, fill=pal["metal"], outline=outline, width=max(1, int(1*S)))
            for dx in (-8, 2, 12):
                d.polygon([(head_center[0] + dx*S, head_center[1] - 28*S), (head_center[0] + (dx+5)*S, head_center[1] - 40*S), (head_center[0] + (dx+10)*S, head_center[1] - 28*S)], fill=pal["tooth"], outline=outline)
        elif "shaman" in name:
            d.arc((head_center[0] - 22*S, head_center[1] - 35*S, head_center[0] + 23*S, head_center[1] - 10*S), start=195, end=345, fill=pal["eye"], width=max(1, int(1.8*S)))
            for dx, dy in [(-18, -34), (3, -39), (23, -31)]:
                d.ellipse((head_center[0] + dx*S - 2*S, head_center[1] + dy*S - 2*S, head_center[0] + dx*S + 2*S, head_center[1] + dy*S + 2*S), fill=pal["eye_glow"])
        elif "scout" in name:
            d.polygon([(head_center[0] - 24*S, head_center[1] - 12*S), (head_center[0] + 11*S, head_center[1] - 25*S), (head_center[0] + 26*S, head_center[1] - 8*S), (head_center[0] + 6*S, head_center[1] - 13*S)], fill=pal["cloth"], outline=outline)
            d.line([(body_center[0] - 16*S, body_center[1] - 3*S), (body_center[0] + 18*S, body_center[1] + 13*S)], fill=pal["cloth_dark"], width=max(1, int(2*S)))
        elif "frost" in name:
            d.rounded_rectangle((head_center[0] - 8*S, head_center[1] + 12*S, head_center[0] + 23*S, head_center[1] + 21*S), radius=3*S, fill=pal["cloth"], outline=outline, width=max(1, int(1*S)))
            for dx in (-10, 6, 20):
                d.line([(head_center[0] + dx*S, head_center[1] + 20*S), (head_center[0] + (dx-4)*S, head_center[1] + 29*S)], fill=pal["cloth"], width=max(1, int(2*S)))
        elif "desert" in name:
            d.rounded_rectangle((head_center[0] - 17*S, head_center[1] - 20*S, head_center[0] + 24*S, head_center[1] - 12*S), radius=4*S, fill=pal["cloth"], outline=outline, width=max(1, int(1*S)))
            d.polygon([(head_center[0] + 17*S, head_center[1] - 18*S), (head_center[0] + 33*S, head_center[1] - 23*S), (head_center[0] + 24*S, head_center[1] - 11*S)], fill=pal["cloth"], outline=outline)
        elif "cave" in name:
            d.rounded_rectangle((body_center[0] - 20*S, body_center[1] - 3*S, body_center[0] - 9*S, body_center[1] + 15*S), radius=3*S, fill=pal["metal"], outline=outline, width=max(1, int(1*S)))
            d.ellipse((head_center[0] + 12*S, head_center[1] - 25*S, head_center[0] + 19*S, head_center[1] - 18*S), fill=pal["eye_glow"], outline=outline, width=max(1, int(0.8*S)))

    # --- layout -----------------------------------------------------------------------

    #: The body's centre above the ground, and the head / hips / shoulders
    #: about it, in 128-frame units (the goblin as it was always drawn).
    BODY_UP = 37.0
    HEAD_AT = (16.0, -25.0)
    HIPS = {"far": (-5.0, 9.0), "near": (7.0, 9.0)}
    SHOULDERS = {"far": (-8.0, -7.0), "near": (8.0, -7.0)}
    BASE_X, GROUND = 60.0, 101.0
    #: Kicks hit with the near foot, the bite with the snout.
    KICKS = frozenset({"attack_down", "air_back", "air_down"})
    BITES = frozenset({"pummel", "dash_attack"})
    PUNCHES = frozenset({"jab_2"})
    #: Rows whose speed lines stream vertically.
    VERTICAL = frozenset({"air_down", "spring_pounce", "meteor"})

    def _layout(self, spec: GoblinSpec, p: GoblinPose, S: float) -> Dict[str, object]:
        """Every joint of the goblin for pose ``p``, in canvas pixels."""
        ground = self.GROUND * S
        root = ((self.BASE_X + p.x) * S, ground + p.y * S)
        body = (root[0] + p.bx * S, root[1] + (-self.BODY_UP + p.by) * S)

        def at(off: Point) -> Point:
            ox, oy = _rot((off[0] * S, off[1] * S), p.spin)
            return (body[0] + ox, body[1] + oy)

        out: Dict[str, object] = {"body": body, "ground": ground, "S": S}
        out["head"] = at((self.HEAD_AT[0] + p.hx, self.HEAD_AT[1] + p.hy))
        for side in ("far", "near"):
            shoulder = at(self.SHOULDERS[side])
            u, l = (p.nu, p.nl) if side == "near" else (p.fu, p.fl)
            elbow, hand = self._limb_chain(shoulder, spec.arm_upper * S, spec.arm_lower * S, u, l)
            out[f"{side}_arm"] = (shoulder, elbow, hand)
            hip = at(self.HIPS[side])
            leg = p.nleg if side == "near" else p.fleg
            knee, ankle, planted = self._leg(spec, hip, leg, S, ground)
            out[f"{side}_leg"] = (hip, knee, ankle, planted)
        return out

    def _ankle_for(self, spec: GoblinSpec, hip: Point, leg, S: float, ground: float) -> Tuple[Point, bool]:
        mode = leg[0]
        if mode == "g":
            lift = (2.0 + spec.foot_h * 0.5 + float(leg[2])) * S
            return ((self.BASE_X + float(leg[1])) * S, ground - lift), True
        if mode == "a":
            _knee, ankle = self._limb_chain(hip, spec.leg_upper * S, spec.leg_lower * S, float(leg[1]), float(leg[2]))
            return ankle, False
        # ("mix", leg_a, leg_b, u): both placed, then blended.
        (pa, ga), (pb, gb) = self._ankle_for(spec, hip, leg[1], S, ground), self._ankle_for(spec, hip, leg[2], S, ground)
        u = float(leg[3])
        return (pa[0] + (pb[0] - pa[0]) * u, pa[1] + (pb[1] - pa[1]) * u), (gb if u >= 0.5 else ga)

    def _leg(self, spec: GoblinSpec, hip: Point, leg, S: float, ground: float) -> Tuple[Point, Point, bool]:
        if leg[0] == "a":
            knee, ankle = self._limb_chain(hip, spec.leg_upper * S, spec.leg_lower * S, float(leg[1]), float(leg[2]))
            return knee, ankle, False
        ankle, planted = self._ankle_for(spec, hip, leg, S, ground)
        knee, _a1, _a2 = self._solve_leg_ik(hip, ankle, spec.leg_upper * S, spec.leg_lower * S, bend_sign=1.0)
        return knee, ankle, planted

    def _weapon_reach(self, spec: GoblinSpec) -> float:
        """How far the held item reaches from the fist (128-frame units)."""
        return {"spear": 29.0, "staff": 29.0, "sword": 25.0, "hammer": 26.0, "bow": 23.0}.get(spec.held_item.lower(), 19.0)

    def _strike_points(self, spec: GoblinSpec, animation: str, p: GoblinPose, S: float) -> List[Point]:
        """What hits on this frame: the weapon from fist to tip, or the boot
        of a kick, or the snout of a bite."""
        lay = self._layout(spec, p, S)
        if animation in self.KICKS:
            _hip, knee, ankle, _ = lay["near_leg"]
            return [knee, ankle, add(ankle, vec(spec.foot_w * S, p.spin + 5.0))]
        if animation in self.BITES:
            hx, hy = lay["head"]
            return [(hx + 12 * S, hy), (hx + 20 * S, hy + 4 * S)]
        if animation in self.PUNCHES:
            _shoulder, elbow, fist = lay["far_arm"]
            return [elbow, fist]
        hand = lay["near_arm"][2]
        reach = self._weapon_reach(spec) * S
        return [add(hand, vec(reach * k, p.wa)) for k in (0.3, 0.65, 1.0)]

    # --- effects ------------------------------------------------------------------------

    def _blit(self, img: Image.Image, key: tuple, size: Tuple[float, float], pivot: Point, paint, at: Point,
              degrees: float = 0.0, opacity: float = 1.0, name: str = "fx") -> None:
        """One effect glyph, painted once (cached by ``key``) and placed."""
        if opacity <= 0.02:
            return
        image, piv = shape_rig.piece(key, (int(math.ceil(size[0])), int(math.ceil(size[1]))), pivot, paint)
        rigdoc.blit_rotated(img, image, piv, at, degrees, min(1.0, opacity), part_name=name)

    def _fx_behind(self, img: Image.Image, spec: GoblinSpec, animation: str, frame_index: int, frame_count: int,
                   p: GoblinPose, lay: Dict[str, object], S: float, pal: Dict[str, Color]) -> None:
        fx = p.fx
        body = lay["body"]
        if fx.get("shield", 0.0) > 0.02:
            r = 30 * S
            self._blit(img, ("goblin_fx_shield", pal["eye"], S), (2 * r + 4, 2 * r + 4), (r + 2, r + 2),
                       lambda d: (d.ellipse((2, 2, 2 * r + 2, 2 * r + 2), fill=with_alpha(pal["eye"], 70),
                                            outline=with_alpha(pal["eye_glow"], 220), width=max(1, int(1.6 * S)))),
                       (body[0] + 2 * S, body[1] - 6 * S), 0.0, fx["shield"], "shield")
        trail = fx.get("trail", 0.0)
        if trail > 0.02 and p.wpn > 0.5 and animation not in MOVES.GOBLIN_LOOPS:
            self._draw_trail(img, spec, animation, frame_index, frame_count, S, pal, trail)

    def _draw_trail(self, img, spec, animation, frame_index, frame_count, S, pal, strength) -> None:
        """The smear the weapon tip swept since the last frame: a fan of
        translucent wedges fading toward where it was."""
        if frame_count < 2 or frame_index == 0:
            return
        t = MOVES.clip_time(animation, frame_index, frame_count)
        dt = 1.0 / (frame_count - 1)
        reach = self._weapon_reach(spec) * S
        outer, inner = [], []
        for k in range(6, -1, -1):
            q = self.pose_at(animation, max(0.0, t - dt * k / 6.0))
            hand = self._layout(spec, q, S)["near_arm"][2]
            outer.append(add(hand, vec(reach, q.wa)))
            inner.append(add(hand, vec(reach * 0.45, q.wa)))
        span = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(outer, outer[1:]))
        if span < 6 * S:
            return
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = blending_draw(layer)
        n = len(outer) - 1
        for k in range(n):
            alpha = int(150 * min(1.0, strength) * (k + 1) / n)
            d.polygon([outer[k], outer[k + 1], inner[k + 1], inner[k]], fill=with_alpha(pal["eye_glow"], alpha))
        d.line(outer[n // 2:], fill=with_alpha(pal["eye"], int(220 * min(1.0, strength))), width=max(1, int(1.6 * S)))
        rigdoc.composite_layer(img, layer, name="trail")

    def _fx_front(self, img: Image.Image, spec: GoblinSpec, animation: str, frame_index: int, frame_count: int,
                  p: GoblinPose, lay: Dict[str, object], S: float, pal: Dict[str, Color]) -> None:
        fx = p.fx
        body, ground, head = lay["body"], lay["ground"], lay["head"]
        t = MOVES.clip_time(animation, frame_index, frame_count)
        outline = pal["outline"]
        spark = fx.get("spark", 0.0)
        if spark > 0.02:
            # On the blade, not past its tip: where the hit lands.
            pts = self._strike_points(spec, animation, p, S)
            at = pts[-2] if len(pts) > 2 else pts[-1]
            r = 9 * S

            def star(d, r=r):
                pts = []
                for k in range(16):
                    ang = math.radians(k * 22.5)
                    rr = r if k % 2 == 0 else r * 0.38
                    pts.append((r + 2 + math.cos(ang) * rr, r + 2 + math.sin(ang) * rr))
                d.polygon(pts, fill=with_alpha(pal["eye_glow"], 255), outline=with_alpha(pal["eye"], 255))

            self._blit(img, ("goblin_fx_spark", pal["eye"], S), (2 * r + 4, 2 * r + 4), (r + 2, r + 2), star, at,
                       22.5 * (frame_index % 2), spark, "spark")
        charge = fx.get("charge", 0.0)
        if charge > 0.02 and p.wpn > 0.5:
            hand = lay["near_arm"][2]
            at = add(hand, vec(self._weapon_reach(spec) * S, p.wa))
            r = 7 * S
            self._blit(img, ("goblin_fx_charge", pal["eye"], S), (2 * r + 4, 2 * r + 4), (r + 2, r + 2),
                       lambda d: (d.ellipse((2, 2, 2 * r + 2, 2 * r + 2), outline=with_alpha(pal["eye"], 255), width=max(1, int(1.6 * S))),
                                  d.line([(r + 2, 2), (r + 2, 2 * r + 2)], fill=with_alpha(pal["eye_glow"], 255), width=max(1, int(1.0 * S))),
                                  d.line([(2, r + 2), (2 * r + 2, r + 2)], fill=with_alpha(pal["eye_glow"], 255), width=max(1, int(1.0 * S)))),
                       at, 360.0 * t, charge, "charge")
        dust = fx.get("dust", 0.0)
        if dust > 0.02:
            for side, fade in (("near", 1.0), ("far", 0.8)):
                ankle = lay[f"{side}_leg"][2]
                self._dust(img, (ankle[0] + 3 * S, min(ground, ankle[1] + 5 * S)), S, dust * fade, f"{side}_dust")
        shock = fx.get("shock", 0.0)
        if shock > 0.02:
            x = self._strike_points(spec, animation, p, S)[-1][0] if p.wpn > 0.5 else body[0] + 14 * S
            rx, ry = 20 * S, 3.5 * S
            self._blit(img, ("goblin_fx_shock", pal["eye"], S), (2 * rx + 4, 2 * ry + 4), (rx + 2, ry + 2),
                       lambda d: d.ellipse((2, 2, 2 * rx + 2, 2 * ry + 2), outline=with_alpha(pal["eye"], 230), width=max(1, int(1.4 * S))),
                       (x, ground), 0.0, shock, "shock")
        hit = fx.get("hit", 0.0)
        if hit > 0.02:
            r = 10 * S

            def burst(d, r=r):
                pts = []
                for k in range(16):
                    ang = math.radians(k * 22.5 - 90)
                    rr = r if k % 2 == 0 else r * 0.4
                    pts.append((r + 2 + math.cos(ang) * rr, r + 2 + math.sin(ang) * rr))
                d.polygon(pts, fill=(255, 236, 120, 255), outline=outline)

            self._blit(img, ("goblin_fx_hit", S), (2 * r + 4, 2 * r + 4), (r + 2, r + 2), burst,
                       (body[0] + 8 * S, body[1] - 4 * S), 0.0, hit, "hit")
        flash = fx.get("flash", 0.0)
        if flash > 0.02:
            r = 22 * S
            self._blit(img, ("goblin_fx_flash", S), (2 * r + 4, 2 * r + 4), (r + 2, r + 2),
                       lambda d: d.ellipse((2, 2, 2 * r + 2, 2 * r + 2), outline=(255, 255, 255, 255), width=max(1, int(2.0 * S))),
                       body, 0.0, flash, "flash")
        stars = fx.get("stars", 0.0)
        if stars > 0.02:
            for k in range(3):
                ang = math.tau * (k / 3.0 + t)
                at = (head[0] + 12 * S * math.cos(ang), head[1] - 16 * S + 4 * S * math.sin(ang))
                self._small_star(img, at, S, pal, stars, f"star{k}")
        if animation == "sleep" or fx.get("zzz", 0.0) > 0.02:
            for k in range(2):
                u = (t + k / 2.0) % 1.0
                at = (head[0] + 6 * S + 6 * S * u, head[1] - 16 * S - 14 * S * u)
                self._blit(img, ("goblin_fx_z", S), (10 * S, 10 * S), (5 * S, 5 * S),
                           lambda d: d.line([(2 * S, 2 * S), (8 * S, 2 * S), (2 * S, 8 * S), (8 * S, 8 * S)],
                                            fill=(220, 240, 255, 255), width=max(1, int(1.4 * S))),
                           at, -10.0, math.sin(math.pi * u), f"z{k}")
        rock = fx.get("rock", 0.0)
        if 0.0 < rock < 0.999:
            q = self.pose_at(animation, 0.5)
            start = self._layout(spec, q, S)["far_arm"][2]
            at = (start[0] + 42 * S * rock, start[1] - 18 * S * math.sin(math.pi * rock) + 10 * S * rock)
            r = 3.5 * S
            self._blit(img, ("goblin_fx_rock", S), (2 * r + 4, 2 * r + 4), (r + 2, r + 2),
                       lambda d: d.polygon([(2, r + 2), (r, 2), (2 * r + 2, r), (2 * r, 2 * r + 2), (r - 1, 2 * r + 2)],
                                           fill=(128, 118, 104, 255), outline=outline),
                       at, 300.0 * rock, 1.0, "rock")
        elif rock >= 0.999:
            pass
        if fx.get("rock", 0.0) > 0.0 and fx.get("rock", 0.0) < 0.05:
            # Still in the fist.
            pass
        mound = fx.get("mound", 0.0)
        if mound > 0.02:
            w, h = 30 * S, 12 * S
            self._blit(img, ("goblin_fx_mound", S), (2 * w + 4, h + 4 * S + 4), (w + 2, h * 0.5 + 2),
                       lambda d: (d.pieslice((2, 2, 2 * w + 2, 2 * h + 2), 180, 360, fill=(110, 82, 56, 255), outline=outline),
                                  d.rectangle((2, h + 2, 2 * w + 2, h + 4 * S + 2), fill=(110, 82, 56, 255))),
                       (body[0], ground - h * 0.5 + 2 * S), 0.0, mound, "mound")

    def _dust(self, img, at: Point, S: float, opacity: float, name: str) -> None:
        r = 5 * S

        def paint(d, r=r):
            for dx, dy, k in ((-3, 1, 0.8), (0, -1, 1.0), (3, 1, 0.8)):
                rr = r * k
                cx, cy = 2 * r + dx * S, r + dy * S
                d.ellipse((cx - rr, cy - rr * 0.7, cx + rr, cy + rr * 0.7), fill=(176, 150, 108, 200))

        self._blit(img, ("goblin_fx_dust", S), (4 * r, 2 * r), (2 * r, r), paint, at, 0.0, opacity, name)

    def _small_star(self, img, at: Point, S: float, pal, opacity: float, name: str) -> None:
        r = 3.5 * S

        def paint(d, r=r):
            pts = []
            for k in range(10):
                ang = math.radians(k * 36 - 90)
                rr = r if k % 2 == 0 else r * 0.45
                pts.append((r + 2 + math.cos(ang) * rr, r + 2 + math.sin(ang) * rr))
            d.polygon(pts, fill=(255, 214, 92, 255), outline=pal["outline"])

        self._blit(img, ("goblin_fx_star", S), (2 * r + 4, 2 * r + 4), (r + 2, r + 2), paint, at, 0.0, opacity, name)

    # --- hit volumes ----------------------------------------------------------------------

    def attack_hitboxes(self, size: Tuple[int, int]) -> Dict[str, Dict[str, object]]:
        """Each strike row's volume, measured from where the weapon (or boot,
        or teeth) actually is on its active frames, in source-canvas pixels.
        The first active frame counts only the last 30% of its approach (the
        rest is still the wind-up); a strike already under way counts all of
        it."""
        spec = getattr(self, "_last_spec", None)
        if spec is None:
            return {}
        S = size[0] / 128.0
        out: Dict[str, Dict[str, object]] = {}
        for name, frames, _ms in GOBLIN_ROWS:
            if name in MOVES.GOBLIN_LOOPS or name not in MOVES.MOVES:
                continue
            dt = 1.0 / max(1, frames - 1)
            active: List[int] = []
            points: List[Point] = []
            for i in range(frames):
                t = MOVES.clip_time(name, i, frames)
                p = self.pose_at(name, t)
                if not (p.fx.get("trail", 0.0) >= 0.5 or p.fx.get("spark", 0.0) >= 0.75):
                    continue
                span = 1.0 if active and active[-1] == i - 1 else 0.3
                active.append(i)
                for k in range(4):
                    q = self.pose_at(name, max(0.0, t - dt * span * k / 3.0))
                    # Each point a small square: a thrust that moves straight
                    # along its own line still has a volume.
                    r = 3.0 * S
                    for x, y in self._strike_points(spec, name, q, S):
                        points += [(x - r, y - r), (x + r, y - r), (x + r, y + r), (x - r, y + r)]
            if not active:
                continue
            poly = _hull(points)
            if len(poly) < 3:
                continue
            xs, ys = [q[0] for q in poly], [q[1] for q in poly]
            x0, y0 = int(math.floor(min(xs))), int(math.floor(min(ys)))
            x1, y1 = int(math.ceil(max(xs))), int(math.ceil(max(ys)))
            out[name] = {"active_frames": active, "bbox": (x0, y0, x1 - x0, y1 - y0),
                         "poly": [(round(x, 2), round(y, 2)) for x, y in poly]}
        return out

    # --- the frame --------------------------------------------------------------------------

    def _render_highres(self, spec: GoblinSpec, animation: str, frame_index: int, frame_count: int, size: Tuple[int, int], background: Optional[Color], scale: int) -> Image.Image:
        W, H = size[0] * scale, size[1] * scale
        bg = (0, 0, 0, 0) if background is None else background
        img = Image.new("RGBA", (W, H), bg)
        # Scale the 128-base character to the requested frame width so a
        # render_scale>1 canvas draws the SAME character with more native
        # pixels (matches the toon generator's S=(W/128)*ss). Identical at the
        # 128 default; only render_scale>1 changes it.
        S = float(scale) * (size[0] / 128.0)
        pal = self.PALETTES.get(spec.palette_name, self.PALETTES["classic"])
        p = self.pose_for_animation(animation, frame_index, frame_count)
        lay = self._layout(spec, p, S)
        ground_y = lay["ground"]
        root_x = (self.BASE_X + p.x) * S
        # No baked ground drop shadow; the scene renderer owns contact shadows.

        # The teleport glyphs as one effect piece a frame (not one draw a stroke).
        if animation in {"blink_out", "blink_in"}:
            fx = self._draw_blink_out_fx if animation == "blink_out" else self._draw_blink_in_fx
            part = shape_rig.piece(
                ("goblin_blink_fx", animation, frame_index, frame_count, round(root_x, 3), round(ground_y, 3), spec.palette_name, img.size),
                img.size,
                (0.0, 0.0),
                lambda dd: fx(dd._img, root_x, ground_y, S, frame_index, frame_count, pal),
            )
            shape_rig.place(img, part, (0.0, 0.0), 0.0, "blink_fx")

        speed = p.fx.get("speed", 0.0)
        if speed > 0.02:
            # Speed lines: each one piece (its length) slid to its height,
            # streaming off behind the body.
            body = lay["body"]
            vertical = animation in self.VERTICAL
            for i in range(4):
                y = body[1] + (-12 + i * 8 + math.sin(frame_index + i) * 2) * S
                span, lpad = (26 - i * 3) * S, 3 * S
                line = shape_rig.piece(
                    ("goblin_speed_line", i, round(S, 4)),
                    (span + 2 * lpad, 2 * lpad + 2 * S),
                    (lpad, lpad + 2 * S),
                    lambda dd, span=span, lpad=lpad: dd.line([(lpad, lpad + 2 * S), (lpad + span, lpad)], fill=(150, 212, 105, 90), width=max(1, int(1.5 * S))),
                )
                if vertical:
                    # Streaming off whichever way the goblin is not going.
                    up = -1.0 if animation == "air_down" else 1.0
                    at = (body[0] + (-12 + i * 8) * S, body[1] - up * (46 - i * 2) * S)
                    rigdoc.blit_rotated(img, line[0], line[1], at, 90.0 * up, min(1.0, speed), part_name=f"speed_line{i}")
                else:
                    rigdoc.blit_rotated(img, line[0], line[1], (body[0] - (46 - i * 2) * S, y), 0.0, min(1.0, speed),
                                        part_name=f"speed_line{i}")

        character_img = img if animation not in {"blink_out", "blink_in"} else Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self._fx_behind(character_img, spec, animation, frame_index, frame_count, p, lay, S, pal)

        # Legs: far, then near.
        for side, tint, shift in (("far", pal["skin_shadow"], -1.5), ("near", pal["skin"], 3.0)):
            hip, knee, ankle, planted = lay[f"{side}_leg"]
            shape_rig.capsule(character_img, hip, knee, 2.5 * S, tint, pal["outline"], 1.2 * S, f"{side}_thigh", length=spec.leg_upper * S)
            shape_rig.capsule(character_img, knee, ankle, 2.3 * S, tint, pal["outline"], 1.2 * S, f"{side}_shin", length=spec.leg_lower * S)
            leg = p.nleg if side == "near" else p.fleg
            # A planted foot lies flat; a foot in the air follows its shin.
            foot_cw = 5.0 if planted else 5.0 + (math.degrees(math.atan2(ankle[1] - knee[1], ankle[0] - knee[0])) - 90.0) * 0.6
            ox, oy = _rot(((spec.foot_w * 0.32 + shift) * S, 2.0 * S), foot_cw - 5.0)
            foot_center = (ankle[0] + ox, ankle[1] + oy)
            if planted:
                foot_center = (foot_center[0], min(ground_y - 2 * S, foot_center[1]))
            del leg
            draw_rotated_rounded_rect(character_img, foot_center, (spec.foot_w * S, spec.foot_h * S), -foot_cw, spec.foot_h * 0.5 * S, tint, pal["outline"], 1.1 * S, name=f"{side}_foot")

        # Far arm behind body (or, reaching across, in front of it).
        def far_arm() -> None:
            shoulder, elbow, hand = lay["far_arm"]
            shape_rig.capsule(character_img, shoulder, elbow, 2.2 * S, pal["skin_shadow"], pal["outline"], 1.1 * S, "far_upper_arm", length=spec.arm_upper * S)
            shape_rig.capsule(character_img, elbow, hand, 2.1 * S, pal["skin_shadow"], pal["outline"], 1.1 * S, "far_forearm", length=spec.arm_lower * S)

        if p.fz < 0.5:
            far_arm()
        hand = lay["far_arm"][2]
        if 0.0 < p.fx.get("rock", 0.0) < 0.05:
            # The rock in the fist before it flies.
            r = 3.5 * S
            self._blit(character_img, ("goblin_fx_rock", S), (2 * r + 4, 2 * r + 4), (r + 2, r + 2),
                       lambda d: d.polygon([(2, r + 2), (r, 2), (2 * r + 2, r), (2 * r, 2 * r + 2), (r - 1, 2 * r + 2)],
                                           fill=(128, 118, 104, 255), outline=pal["outline"]),
                       hand, 0.0, 1.0, "rock_held")

        body_center, head_center = lay["body"], lay["head"]
        self._draw_body(character_img, body_center, spec, pal, S, -(p.tilt + p.spin), p.spin)
        self._draw_rigid_head(character_img, head_center, spec, pal, S, -(p.head + p.spin), p.blink, p.squint, p.dead, p.mouth)
        self._place_variant_accessories(character_img, spec, pal, S, body_center, head_center, p.spin, p.head + p.spin)
        if p.fz >= 0.5:
            far_arm()

        # Near arm and weapon on top.
        shoulder, elbow, hand = lay["near_arm"]
        shape_rig.capsule(character_img, shoulder, elbow, 2.3 * S, pal["skin"], pal["outline"], 1.1 * S, "near_upper_arm", length=spec.arm_upper * S)
        shape_rig.capsule(character_img, elbow, hand, 2.2 * S, pal["skin"], pal["outline"], 1.1 * S, "near_forearm", length=spec.arm_lower * S)
        hand_r = spec.hand_r * S
        hand_pad = hand_r + 2 * S
        hand_part = shape_rig.piece(
            ("goblin_hand", round(hand_r, 3), pal["skin"], pal["outline"], S),
            (2 * hand_pad, 2 * hand_pad),
            (hand_pad, hand_pad),
            lambda d: d.ellipse((hand_pad - hand_r, hand_pad - hand_r, hand_pad + hand_r, hand_pad + hand_r), fill=pal["skin"], outline=pal["outline"], width=max(1, int(1.0 * S))),
        )
        shape_rig.place(character_img, hand_part, hand, 0.0, "near_hand")
        if p.wpn > 0.5:
            self._place_weapon(character_img, hand, spec, pal, S, p.wa)
        self._fx_front(character_img, spec, animation, frame_index, frame_count, p, lay, S, pal)

        if animation in {"blink_out", "blink_in"}:
            self._composite_teleport_actor(img, character_img, animation, frame_index, frame_count, S)
        return img

    @profile
    def render_animation_frame(
        self,
        spec: GoblinSpec,
        animation: str,
        frame_index: int,
        frame_count: int,
        size: Tuple[int, int] = (128, 128),
        background: Optional[Color] = None,
        supersample: int = 4,
        downsample: str = "lanczos",
    ) -> Image.Image:
        high = self._render_highres(spec, animation, frame_index, frame_count, size, background, max(1, int(supersample)))
        resample = RESAMPLING.NEAREST if downsample == "nearest" else RESAMPLING.LANCZOS
        return rigdoc.downsampled_canvas(high, size, resample)

    @profile
    def render_frame(
        self,
        spec: GoblinSpec,
        animation: str,
        frame_index: int,
        size: Tuple[int, int],
        job: CharacterJob,
    ) -> Image.Image:
        anim = self.animations()[animation]
        return self.render_animation_frame(
            spec,
            animation,
            frame_index % anim["frames"],
            anim["frames"],
            size,
            background=parse_background(job.render.background),
            supersample=job.render.supersample,
            downsample=job.render.downsample,
        )
