"""Opaque right-facing green goblin target for side-scrolling games.

The goblin's look is one of ``_goblin_look.LOOKS`` (the default, the Smash
skins, the heavies, Fretjaw and the hall's goblins), chosen from the
archetype or named by a config's ``spec_overrides: {look: ...}``. Its MOVES
are key poses in ``_goblin_moves.py`` (a full platform-fighter moveset: a
stabbing jab string, tilts, smashes, aerials, specials, grabs and throws,
shield and dodges, the damage, ledge, item and presentation rows) and its
rows and fighter-category coverage are ``_goblin_motion.py``. A pose is laid
out here (``_layout``: the whole goblin can turn about its body, legs plant
by IK or tuck by angle, the weapon points anywhere) and its look's parts are
placed on it. Swing smears, sparks, dust and the rest are drawn from
the pose's ``fx`` strengths, and ``attack_hitboxes`` measures each strike's
volume from where the weapon (or boot, or teeth) is on its active frames.

The ``blink_out`` and ``blink_in`` rows are Ambition's short-range teleport /
precision-blink ability split into source and destination phases, not an eyelid
blink.  The goblin remains fully opaque inside the character
silhouette; translucent pixels are reserved for outer antialiasing and FX.

For this right-facing target, the far arm is drawn behind the body and the near
weapon arm is drawn in front.  The head is one rigid part turned as a unit, so
ears, nose, eye, mouth and teeth do not shear apart.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from PIL import Image
from ambition_sprite2d_renderer.core.draw import rgba, with_alpha

from ...profiling import profile
from ...authoring import rigdoc, shape_rig
from ...authoring.common_draw import RESAMPLING
from ...authoring.generator import CharacterGenerator
from ...authoring.rig import add, clamp, ease_out_cubic, smoothstep, vec
from ...registry import CharacterJob
from . import _goblin_look as LOOK
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


@dataclass(frozen=True)
class GoblinSpec:
    target: str
    seed: int
    archetype: str
    held_item: str
    #: The ``_goblin_look.LOOKS`` entry it is drawn as.
    look: str
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

    def build_spec(self, job: CharacterJob) -> GoblinSpec:
        seed, archetype, held_item = job.seed, job.archetype, job.held_item
        rng = random.Random(seed)
        archetype_key = str(archetype or "default").lower()
        look = LOOK.look_for_archetype(archetype)
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
            look=look,
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


    # --- layout -----------------------------------------------------------------------

    #: The body's centre above the ground, and the head / hips / shoulders
    #: about it, in 128-frame units (the goblin as it was always drawn; a
    #: look may move the head and shoulders, ``_goblin_look`` ``layout``).
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

    def _figure(self, spec: GoblinSpec, S: float) -> Tuple[float, Point]:
        """The figure's scale and where its feet's centre (``BASE_X`` on the
        ground) lands, for a canvas of ``S`` pixels a 128-frame unit. A look
        drawn bigger (``k``) scales about its feet on a canvas ``canvas``
        times the frame, the extra room above it and to both sides."""
        look = LOOK.LOOKS[spec.look]
        c = look["canvas"]
        return S * look["k"], ((self.BASE_X + (c - 1.0) * 64.0) * S, (self.GROUND + (c - 1.0) * 128.0) * S)

    def _layout(self, spec: GoblinSpec, p: GoblinPose, S: float) -> Dict[str, object]:
        """Every joint of the goblin for pose ``p``, in canvas pixels; ``Sk``
        is the figure's own scale."""
        Sk, (fx0, ground) = self._figure(spec, S)
        place = LOOK.LOOKS[spec.look]["layout"]
        head_at, shoulders = place.get("head_at", self.HEAD_AT), place.get("shoulders", self.SHOULDERS)
        root = (fx0 + p.x * Sk, ground + p.y * Sk)
        body = (root[0] + p.bx * Sk, root[1] + (-self.BODY_UP + p.by) * Sk)

        def at(off: Point) -> Point:
            ox, oy = _rot((off[0] * Sk, off[1] * Sk), p.spin)
            return (body[0] + ox, body[1] + oy)

        out: Dict[str, object] = {"body": body, "ground": ground, "S": S, "Sk": Sk}
        out["head"] = at((head_at[0] + p.hx, head_at[1] + p.hy))
        for side in ("far", "near"):
            shoulder = at(shoulders[side])
            u, l = (p.nu, p.nl) if side == "near" else (p.fu, p.fl)
            elbow, hand = self._limb_chain(shoulder, spec.arm_upper * Sk, spec.arm_lower * Sk, u, l)
            out[f"{side}_arm"] = (shoulder, elbow, hand)
            hip = at(self.HIPS[side])
            leg = p.nleg if side == "near" else p.fleg
            knee, ankle, planted = self._leg(spec, hip, leg, Sk, fx0, ground)
            out[f"{side}_leg"] = (hip, knee, ankle, planted)
        return out

    def _ankle_for(self, spec: GoblinSpec, hip: Point, leg, Sk: float, fx0: float, ground: float) -> Tuple[Point, bool]:
        mode = leg[0]
        if mode == "g":
            lift = (2.0 + spec.foot_h * 0.5 + float(leg[2])) * Sk
            return (fx0 + float(leg[1]) * Sk, ground - lift), True
        if mode == "a":
            _knee, ankle = self._limb_chain(hip, spec.leg_upper * Sk, spec.leg_lower * Sk, float(leg[1]), float(leg[2]))
            return ankle, False
        # ("mix", leg_a, leg_b, u): both placed, then blended.
        (pa, ga), (pb, gb) = (self._ankle_for(spec, hip, leg[1], Sk, fx0, ground),
                              self._ankle_for(spec, hip, leg[2], Sk, fx0, ground))
        u = float(leg[3])
        return (pa[0] + (pb[0] - pa[0]) * u, pa[1] + (pb[1] - pa[1]) * u), (gb if u >= 0.5 else ga)

    def _leg(self, spec: GoblinSpec, hip: Point, leg, Sk: float, fx0: float, ground: float) -> Tuple[Point, Point, bool]:
        if leg[0] == "a":
            knee, ankle = self._limb_chain(hip, spec.leg_upper * Sk, spec.leg_lower * Sk, float(leg[1]), float(leg[2]))
            return knee, ankle, False
        ankle, planted = self._ankle_for(spec, hip, leg, Sk, fx0, ground)
        knee, _a1, _a2 = self._solve_leg_ik(hip, ankle, spec.leg_upper * Sk, spec.leg_lower * Sk, bend_sign=1.0)
        return knee, ankle, planted

    #: How far each held item reaches from the fist (the figure's 128-frame
    #: units); ``_goblin_look`` draws each to it.
    WEAPON_REACH = {"spear": 29.0, "staff": 29.0, "sword": 25.0, "hammer": 26.0, "bow": 23.0, "dagger": 19.0}

    def _weapon_reach(self, spec: GoblinSpec) -> float:
        """How far the held item reaches from the fist, in canvas units."""
        return self.WEAPON_REACH.get(spec.held_item.lower(), 19.0) * LOOK.LOOKS[spec.look]["k"]

    def _strike_points(self, spec: GoblinSpec, animation: str, p: GoblinPose, S: float) -> List[Point]:
        """What hits on this frame: the weapon from fist to tip, or the boot
        of a kick, or the snout of a bite."""
        lay = self._layout(spec, p, S)
        Sk = lay["Sk"]
        if animation in self.KICKS:
            _hip, knee, ankle, _ = lay["near_leg"]
            return [knee, ankle, add(ankle, vec(spec.foot_w * Sk, p.spin + 5.0))]
        if animation in self.BITES:
            hx, hy = lay["head"]
            return [(hx + 12 * Sk, hy), (hx + 20 * Sk, hy + 4 * Sk)]
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
        S = size[0] / (128.0 * LOOK.LOOKS[spec.look]["canvas"])
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
        # pixels (matches the toon generator's S=(W/128)*ss). A look on a
        # bigger canvas (``_goblin_look``) has that much more frame.
        S = float(scale) * (size[0] / (128.0 * LOOK.LOOKS[spec.look]["canvas"]))
        painter = LOOK.Painter(spec.look)
        pal = self._fx_palette(painter.pal)
        p = self.pose_for_animation(animation, frame_index, frame_count)
        lay = self._layout(spec, p, S)
        ground_y, Sk = lay["ground"], lay["Sk"]
        root_x = lay["body"][0] - p.bx * Sk
        # No baked ground drop shadow; the scene renderer owns contact shadows.

        # The teleport glyphs as one effect piece a frame (not one draw a stroke).
        if animation in {"blink_out", "blink_in"}:
            fx = self._draw_blink_out_fx if animation == "blink_out" else self._draw_blink_in_fx
            part = shape_rig.piece(
                ("goblin_blink_fx", animation, frame_index, frame_count, round(root_x, 3), round(ground_y, 3), spec.look, img.size),
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

        self._draw_goblin(character_img, spec, painter, p, lay)
        self._fx_front(character_img, spec, animation, frame_index, frame_count, p, lay, S, pal)

        if animation in {"blink_out", "blink_in"}:
            self._composite_teleport_actor(img, character_img, animation, frame_index, frame_count, S)
        return img

    @staticmethod
    def _fx_palette(look_pal: Dict[str, Color]) -> Dict[str, Color]:
        """The colours the effects draw in, from the look."""
        return {"outline": look_pal["ink"], "eye": look_pal["eye"], "eye_glow": look_pal["eye_glow"],
                "skin": look_pal["skin"], "skin_shadow": look_pal["skin_sh"], "cloth": look_pal["cloth"]}

    def _draw_goblin(self, img: Image.Image, spec: GoblinSpec, painter: "LOOK.Painter", p: GoblinPose, lay: Dict[str, object]) -> None:
        """The look's parts on the laid-out skeleton, back to front: far leg,
        far arm (unless it reaches across), far ear, neck, near leg, body,
        head, then the near arm with the weapon in its fist."""
        Sk, ground_y = lay["Sk"], lay["ground"]
        look, pal, limb = painter.L, painter.pal, painter.L["limb"]

        def group(items) -> None:
            # Every ink before any fill: the segments read as one limb.
            for part, at, deg, name in items:
                shape_rig.place(img, part[0] if isinstance(part[0], tuple) else part, at, deg, name + ("_ink" if isinstance(part[0], tuple) else ""))
            for part, at, deg, name in items:
                if isinstance(part[0], tuple):
                    shape_rig.place(img, part[1], at, deg, name)

        def tones(near: bool):
            return (pal["skin"], pal["skin_sh"]) if near else (pal["skin_far"], pal["skin_far_sh"])

        def limb_items(a, b, c, l1, l2, radii, fill, shade, name, wraps=False, sleeve=None):
            r0, r1, r2 = (r * limb for r in radii)
            upper = painter.segment(Sk, l1, r0, r1, fill, shade) if sleeve is None else painter.segment(Sk, l1, r0 + 0.6, r1 + 0.9, *sleeve)
            return [
                (upper, a, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])), name + "_upper"),
                (painter.segment(Sk, l2, r1, r2, fill, shade, wraps), b, math.degrees(math.atan2(c[1] - b[1], c[0] - b[0])), name + "_lower"),
            ]

        def leg(side: str) -> None:
            hip, knee, ankle, planted = lay[f"{side}_leg"]
            near = side == "near"
            items = limb_items(hip, knee, ankle, spec.leg_upper, spec.leg_lower, (2.7, 1.9, 1.6), *tones(near), f"{side}_leg")
            # A planted foot lies flat on the ground; one in the air follows its shin.
            tilt = 0.0 if planted else (math.degrees(math.atan2(ankle[1] - knee[1], ankle[0] - knee[0])) - 90.0) * 0.6
            at = (ankle[0], min(ankle[1], ground_y - 3.6 * Sk)) if planted else ankle
            items.append((painter.foot(Sk, near), at, tilt, f"{side}_foot"))
            group(items)

        def arm(side: str) -> None:
            shoulder, elbow, hand = lay[f"{side}_arm"]
            near = side == "near"
            sleeve = None
            if look["sleeve"]:
                cloth, cloth_sh = pal[look["sleeve"]], pal[look["sleeve"] + "_sh"]
                sleeve = (cloth, cloth_sh) if near else (cloth_sh, cloth_sh)
            items = limb_items(shoulder, elbow, hand, spec.arm_upper, spec.arm_lower, (2.3, 1.7, 1.5), *tones(near), f"{side}_arm",
                               wraps="wraps" in look["gear"], sleeve=sleeve)
            group(items)
            if near:
                if "pauldron" in look["gear"]:
                    group([(painter.pauldron(Sk), shoulder, p.tilt * 0.5 + p.spin, "pauldron")])
                if p.wpn > 0.5:
                    group([(painter.weapon(Sk, spec.held_item.lower()), hand, p.wa, "weapon")])
            turn = p.wa if (near and p.wpn > 0.5) else math.degrees(math.atan2(hand[1] - elbow[1], hand[0] - elbow[0]))
            group([(painter.hand(Sk, near), hand, turn, f"{side}_hand")])

        leg("far")
        if p.fz < 0.5:
            arm("far")
        body, head = lay["body"], lay["head"]
        head_turn = p.head + p.spin
        group([(painter.far_ear(Sk), head, head_turn, "far_ear")])
        # The neck: from the top of the body to under the head.
        base = add(body, _rot((5.0 * Sk, -8.0 * Sk), p.spin))
        top = add(head, _rot((-4.0 * Sk, 7.0 * Sk), head_turn))
        thick = min(limb, 1.3)
        neck = painter.segment(Sk, round(math.hypot(top[0] - base[0], top[1] - base[1]) / Sk, 1), 3.8 * thick, 3.2 * thick, pal["skin"], pal["skin_sh"])
        group([(neck, base, math.degrees(math.atan2(top[1] - base[1], top[0] - base[0])), "neck")])
        leg("near")
        # The body leans half its tilt (the shoulders do not follow it).
        group([(painter.torso(Sk), body, p.tilt * 0.5 + p.spin, "torso")])
        squint = round(p.squint * 10.0) / 10.0
        # Three jaw states (shut, open, gaping) keep the head pieces few.
        mouth = round(min(1.0, max(0.0, p.mouth)) * 2.0) / 2.0
        group([(painter.head(Sk, p.blink, squint, p.dead, mouth), head, head_turn, "head")])
        if p.fz >= 0.5:
            arm("far")
        arm("near")

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
